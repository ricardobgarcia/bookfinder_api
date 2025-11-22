from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes.health import router as health_router
from .core.data.repository import load_books
from .core.ingestion.scraper import ensure_books_csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life cycle.

    - STARTUP:
      - Ensures the CSV exists.
      - Loads the CSV in memory and sets in app.state.books_cache.

    - SHUTDOWN:
      - Cache clean-up.
    """
    # STARTUP
    print('[LIFESPAN] Starting BookFinder API...')

    ensure_books_csv()
    print('[LIFESPAN] CSV ensured/updated.')

    app.state.books_cache = load_books()
    print(
        f'[LIFESPAN] Books cache loaded with {len(app.state.books_cache)} items.'
    )

    # Delivers the control to the application
    yield

    # SHUTDOWN
    print('[LIFESPAN] Shutting down BookFinder API...')

    # Cache clean-up.
    if hasattr(app.state, "books_cache"):
        cache_len = len(app.state.books_cache)
        app.state.books_cache.clear()
        print(f'[LIFESPAN] Cleared books cache ({cache_len} entries).')

    print('[LIFESPAN] Shutdown complete.')


app = FastAPI(
    title='BookFinder API',
    description='Public API for querying book data scraped from books.toscrape.com',
    version='0.1.0',
    lifespan=lifespan
)

app.include_router(health_router)
