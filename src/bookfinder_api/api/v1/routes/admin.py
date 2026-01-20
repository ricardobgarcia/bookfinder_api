from fastapi import APIRouter, Request, status

from ....core.ingestion.scraper import scrape_all_books_to_csv, get_csv_status
from ....core.data.repository import load_books

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scrape", status_code=status.HTTP_201_CREATED)
def run_scrape(request: Request):
    """
    Run the scraper to generate/update the database.
    """
    scrape_all_books_to_csv()
    request.app.state.books_cache = load_books()
    csv_status = get_csv_status()
    books_cache = request.app.state.books_cache

    return {
        "status": "ok",
        "message": "Scraping finished and CSV updated.",
        "csv_status": {
            "exists": csv_status["exists"],
            "is_fresh": csv_status["is_fresh"],
            "last_updated": (
                csv_status["last_updated"].isoformat()
                if csv_status["last_updated"] else None
            ),
            "age_seconds": csv_status["age_seconds"],
        },
        "total_books": len(books_cache),
    }
