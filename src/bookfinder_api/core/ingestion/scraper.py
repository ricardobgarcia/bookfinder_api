import csv
import re
from dataclasses import  asdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Iterator, List, Dict
from urllib.parse import urljoin


import requests
from bs4 import BeautifulSoup

from ..models.Book import Book


BASE_URL = "https://books.toscrape.com/"
DATA_DIR = Path(__file__).resolve().parents[4] / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "books.csv"
MAX_AGE = timedelta(days=1)


def get_csv_status():
    exists = CSV_PATH.exists()
    last_updated = None
    age_seconds = None

    if exists:
        mtime = datetime.fromtimestamp(CSV_PATH.stat().st_mtime)
        last_updated = mtime
        age_seconds = (datetime.now() - mtime).total_seconds()

    return {
        "exists": exists,
        "is_fresh": is_csv_fresh() if exists else False,
        "last_updated": last_updated,
        "age_seconds": age_seconds,
        "path": str(CSV_PATH),
    }


def is_csv_fresh() -> bool:
    if not CSV_PATH.exists():
        return False
    mtime = datetime.fromtimestamp(CSV_PATH.stat().st_mtime)
    return datetime.now() - mtime < MAX_AGE


def ensure_books_csv():
    if not is_csv_fresh():
        scrape_all_books_to_csv()


def scrape_all_books_to_csv():
    books = scrape_all_books()
    write_books_to_csv(books)


def scrape_all_books() -> List[Book]:
    all_books: List[Book] = []

    for cat in iter_categories():
        category_name = cat["name"]
        category_url = cat["url"]

        for page_soup in iter_category_pages(category_url):
            page_books = parse_book_list_page(page_soup, category_name)
            all_books.extend(page_books)

    return all_books


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def iter_categories() -> Iterator[Dict[str, str]]:
    """
    Generate dicts {"name": <category_name>, "url": <category_url>}
    """
    soup = get_soup(BASE_URL)
    ul = soup.select_one("ul.nav-list > li > ul")
    if not ul:
        return

    for li in ul.select("li > a"):
        name = li.get_text(strip=True)
        href = li.get("href")
        if not href:
            continue
        url = urljoin(BASE_URL, href)
        yield {"name": name, "url": url}


def iter_category_pages(category_url: str) -> Iterator[BeautifulSoup]:
    current_url = category_url

    while True:
        soup = get_soup(current_url)
        yield soup

        next_link = soup.select_one("li.next > a")
        if not next_link:
            break

        href = next_link.get("href")
        current_url = urljoin(current_url, href)


def parse_book_list_page(soup: BeautifulSoup, category_name: str) -> List[Book]:
    books: List[Book] = []

    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 > a")
        title = a_tag.get("title", "").strip() if a_tag else ""

        price_tag = article.select_one("p.price_color")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price_value = 0.0
        if price_text:
            price_value = parse_price(price_text)

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
        image_url = urljoin(BASE_URL, img_src)

        book = Book(
            title=title,
            price=price_value,
            rating=rating_value,
            availability=availability,
            category=category_name,
            image_url=image_url,
        )
        books.append(book)

    return books


def write_books_to_csv(books: List[Book]) -> None:
    fieldnames = list(Book.__dataclass_fields__.keys())

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for book in books:
            writer.writerow(asdict(book))


def parse_price(price_text: str) -> float:
    clean = re.sub(r"[^0-9.]", "", price_text)
    return float(clean) if clean else 0.0


def rating_to_int(rating_class: str) -> int:
    mapping = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }
    return mapping.get(rating_class, 0)
