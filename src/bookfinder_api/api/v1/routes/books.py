from typing import List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Request

from ....core.models.Book import Book
from ..schemas.BookOut import BookOut
from ..schemas.PaginatedBooks import PaginatedBooks

router = APIRouter(prefix="/books", tags=["books"])


def to_book_out(book: Book, idx: int) -> BookOut:
    return BookOut(
        id=idx,
        title=book.title,
        price=book.price,
        rating=book.rating,
        availability=book.availability,
        category=book.category,
        image_url=book.image_url,
    )

@router.get("", response_model=PaginatedBooks)
def list_books(
    request: Request,
    q: Optional[str] = Query(
        None, description="Search text in book title (case-insensitive)"
    ),
    category: Optional[str] = Query(
        None, description="Exact category name (case-insensitive)"
    ),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List books in catalog.
    """
    books: List[BookOut] = request.app.state.books_cache

    indexed: List[Tuple[int, Book]] = list(enumerate(books))

    if q:
        q_lower = q.lower()
        indexed = [(i, b) for i, b in indexed if q_lower in b.title.lower()]

    if category:
        cat_lower = category.lower()
        indexed = [(i, b) for i, b in indexed if b.category.lower() == cat_lower]

    if min_price is not None:
        indexed = [(i, b) for i, b in indexed if b.price >= min_price]

    if max_price is not None:
        indexed = [(i, b) for i, b in indexed if b.price <= max_price]

    if min_rating is not None:
        indexed = [(i, b) for i, b in indexed if b.rating >= min_rating]

    total = len(indexed)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = indexed[start:end]

    items = [to_book_out(book, idx) for idx, book in page_items]

    return PaginatedBooks(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )

@router.get("/top-rated", response_model=List[BookOut])
def top_rated_books(
    request: Request,
    limit: int = Query(20, ge=1, le=200, description="Max number of books returned"),
    min_rating: int = Query(5, ge=1, le=5, description="Minimum rating threshold"),
):
    """
    List the top-rated books.
    """
    books: List[Book] = request.app.state.books_cache
    indexed: List[Tuple[int, Book]] = list(enumerate(books))

    indexed = [(i, b) for i, b in indexed if b.rating >= min_rating]

    indexed.sort(key=lambda x: (-x[1].rating, x[1].price, x[1].title.lower()))

    top = indexed[:limit]
    return [to_book_out(b, i) for i, b in top]

@router.get("/price-range", response_model=PaginatedBooks)
def books_price_range(
    request: Request,
    min_price: float = Query(..., alias="min", ge=0, description="Minimum price"),
    max_price: float = Query(..., alias="max", ge=0, description="Maximum price"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List books within a given price range.
    """
    if min_price > max_price:
        raise HTTPException(status_code=400, detail="'min' cannot be greater than 'max'")

    books: List[Book] = request.app.state.books_cache
    indexed: List[Tuple[int, Book]] = list(enumerate(books))

    indexed = [(i, b) for i, b in indexed if min_price <= b.price <= max_price]

    indexed.sort(key=lambda x: (x[1].price, x[1].title.lower()))

    total = len(indexed)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = indexed[start:end]

    items = [to_book_out(b, i) for i, b in page_items]

    return PaginatedBooks(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )

@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, request: Request):
    """
    Select book by id.
    """
    books: List[Book] = request.app.state.books_cache

    if book_id < 0 or book_id >= len(books):
        raise HTTPException(status_code=404, detail="Book not found")

    return to_book_out(books[book_id], book_id)
