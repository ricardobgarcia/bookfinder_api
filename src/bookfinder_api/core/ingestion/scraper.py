import asyncio
import csv
import os
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models.Book import Book

BASE_URL = "https://books.toscrape.com/"
MAX_AGE = timedelta(days=1)

# Ajuste fino para Vercel (I/O paralelo, sem exagerar)
DEFAULT_CONCURRENCY = int(os.getenv("SCRAPER_CONCURRENCY", "8"))
HTTP_TIMEOUT = float(os.getenv("SCRAPER_TIMEOUT", "10"))


def _seed_csv_path() -> Path:
    """Load initial CSV file from repo (read-only in Vercel)."""
    return Path(__file__).resolve().parents[4] / "data" / "books.csv"


def _data_dir() -> Path:
    if os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None:
        return Path("/tmp") / "bookfinder_api" / "data"
    return Path(__file__).resolve().parents[4] / "data"


def _csv_path() -> Path:
    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "books.csv"


def get_csv_status():
    csv_path = _csv_path()
    exists = csv_path.exists()
    last_updated = None
    age_seconds = None

    if exists:
        mtime = datetime.fromtimestamp(csv_path.stat().st_mtime)
        last_updated = mtime
        age_seconds = (datetime.now() - mtime).total_seconds()

    return {
        "exists": exists,
        "is_fresh": is_csv_fresh() if exists else False,
        "last_updated": last_updated,
        "age_seconds": age_seconds,
        "path": str(csv_path),
    }


def is_csv_fresh() -> bool:
    csv_path = _csv_path()
    if not csv_path.exists():
        return False
    mtime = datetime.fromtimestamp(csv_path.stat().st_mtime)
    return datetime.now() - mtime < MAX_AGE


def ensure_books_csv(force: bool = False):
    csv_path = _csv_path()
    seed_path = _seed_csv_path()

    if not csv_path.exists() and seed_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(seed_path, csv_path)

    if force or not is_csv_fresh():
        scrape_all_books_to_csv(csv_path)


def scrape_all_books_to_csv(csv_path: Path):
    books = scrape_all_books()

    tmp_path = csv_path.with_suffix(".tmp")
    write_books_to_csv(books, tmp_path)
    tmp_path.replace(csv_path)


def scrape_all_books() -> List[Book]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(scrape_all_books_async(concurrency=DEFAULT_CONCURRENCY))

    return loop.run_until_complete(scrape_all_books_async(concurrency=DEFAULT_CONCURRENCY))


async def scrape_all_books_async(concurrency: int = DEFAULT_CONCURRENCY) -> List[Book]:
    sem = asyncio.Semaphore(max(1, concurrency))

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(HTTP_TIMEOUT),
        headers={"User-Agent": "BookFinderBot/1.0"},
        follow_redirects=True,
    ) as client:
        categories = await fetch_categories(client, sem)

        tasks = [
            scrape_category_all_pages(client, sem, cat_name=cat["name"], cat_url=cat["url"])
            for cat in categories
        ]

        results = await asyncio.gather(*tasks)
        all_books: List[Book] = []
        for books in results:
            all_books.extend(books)
        return all_books


async def fetch_soup(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> BeautifulSoup:
    async with sem:
        resp = await client.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")


async def fetch_categories(client: httpx.AsyncClient, sem: asyncio.Semaphore) -> List[Dict[str, str]]:
    soup = await fetch_soup(client, sem, BASE_URL)
    ul = soup.select_one("ul.nav-list > li > ul")
    if not ul:
        return []

    out: List[Dict[str, str]] = []
    for li in ul.select("li > a"):
        name = li.get_text(strip=True)
        href = li.get("href")
        if not href:
            continue
        url = urljoin(BASE_URL, href)
        out.append({"name": name, "url": url})
    return out


async def scrape_category_all_pages(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    cat_name: str,
    cat_url: str,
) -> List[Book]:
    books: List[Book] = []
    current_url: Optional[str] = cat_url

    while current_url:
        soup = await fetch_soup(client, sem, current_url)
        books.extend(parse_book_list_page(soup, cat_name))

        next_link = soup.select_one("li.next > a")
        if not next_link:
            break

        href = next_link.get("href")
        if not href:
            break

        current_url = urljoin(current_url, href)

    return books


def parse_book_list_page(soup: BeautifulSoup, category_name: str) -> List[Book]:
    books: List[Book] = []

    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 > a")
        title = a_tag.get("title", "").strip() if a_tag else ""

        price_tag = article.select_one("p.price_color")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price_value = parse_price(price_text) if price_text else 0.0

        rating_tag = article.select_one("p.star-rating")
        rating_value = 0
        if rating_tag:
            classes = rating_tag.get("class", [])
            if len(classes) > 1:
                rating_value = rating_to_int(classes[1])

        avail_tag = article.select_one("p.instock.availability")
        availability = avail_tag.get_text(strip=True) if avail_tag else ""

        img_tag = article.select_one("img")
        img_src = img_tag.get("src") if img_tag else ""
        image_url = urljoin(BASE_URL, img_src) if img_src else ""

        books.append(
            Book(
                title=title,
                price=price_value,
                rating=rating_value,
                availability=availability,
                category=category_name,
                image_url=image_url,
            )
        )

    return books


def write_books_to_csv(books: List[Book], path: Path) -> None:
    fieldnames = list(Book.__dataclass_fields__.keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for book in books:
            writer.writerow(asdict(book))


def parse_price(price_text: str) -> float:
    clean = re.sub(r"[^0-9.]", "", price_text)
    return float(clean) if clean else 0.0


def rating_to_int(rating_class: str) -> int:
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    return mapping.get(rating_class, 0)
