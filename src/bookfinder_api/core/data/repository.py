import csv
from typing import List

from bookfinder_api.core.models.Book import Book
from ..ingestion.scraper import _csv_path_readonly, _csv_path
from ..storage.supabase_storage import download_csv


def load_books() -> List[Book]:
    csv_path = _csv_path_readonly()

    if not csv_path.exists():
        data = download_csv()
        csv_path = _csv_path()
        csv_path.write_bytes(data)

    books: List[Book] = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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
