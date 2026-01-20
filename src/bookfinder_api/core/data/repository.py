import csv
from typing import List, Dict

from bookfinder_api.core.models.Book import Book
from ..ingestion.scraper import ensure_books_csv, _csv_path


def load_books() -> List[Dict]:
    ensure_books_csv(force=False)
    csv_path = _csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    books: List[Book] = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            books.append(
                Book(
                    title=row["title"],
                    price=float(row["price"]),
                    rating=int(row["rating"]),
                    availability=row["availability"],
                    category=row["category"],
                    image_url=row["image_url"],
                )
            )

    return books
