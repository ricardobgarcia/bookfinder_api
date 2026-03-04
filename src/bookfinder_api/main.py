from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from .api.v1.router import router as v1_router
from .core.data.repository import load_books


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life cycle.

    - STARTUP:
      - Loads the CSV in memory if exists and sets in app.state.books_cache.

    - SHUTDOWN:
      - Cache clean-up.
    """
    # STARTUP
    print('[LIFESPAN] Starting BookFinder API...')

    try:
        try:
            app.state.books_cache = load_books()
            print(f"[LIFESPAN] Books cache loaded with {len(app.state.books_cache)} items.")
        except Exception as e:
            app.state.books_cache = []
            print(f"[LIFESPAN] Could not load books ({type(e).__name__}: {e}). Cache starts empty. Run /admin/scrape.")

        # Delivers the control to the application
        yield

    finally:
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

app.include_router(v1_router)
