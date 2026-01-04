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
    books: List[BookOut] = request.app.state.books_cache

    # Use (idx, book) for id consistency after filtering
    indexed: List[Tuple[int, Book]] = list(enumerate(books))

    # filtros
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

    # paginação
    total = len(indexed)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = indexed[start:end]

    # converte domínio -> schema v1
    items = [to_book_out(book, idx) for idx, book in page_items]

    return PaginatedBooks(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, request: Request):
    books: List[Book] = request.app.state.books_cache

    if book_id < 0 or book_id >= len(books):
        raise HTTPException(status_code=404, detail="Book not found")

    return to_book_out(books[book_id], book_id)
