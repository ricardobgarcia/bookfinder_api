import csv
from typing import List, Dict

from ...schemas.BookOut import BookOut
from ..ingestion.scraper import CSV_PATH


def load_books() -> List[Dict]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

    books: List[BookOut] = []

    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            books.append(
                BookOut(
                    id=idx,
                    title=row["title"],
                    price=float(row["price"]),
                    rating=int(row["rating"]),
                    availability=row["availability"],
                    category=row["category"],
                    image_url=row["image_url"],
                )
            )

    return books
