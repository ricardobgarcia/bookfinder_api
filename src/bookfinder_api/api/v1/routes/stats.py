from collections import Counter, defaultdict
from typing import List

from fastapi import APIRouter, Request

from bookfinder_api.core.models.Book import Book
from bookfinder_api.api.v1.schemas.StatsOverviewOut import StatsOverviewOut
from bookfinder_api.api.v1.schemas.StatsCategoryOut import StatsCategoriesOut
from bookfinder_api.api.v1.schemas.CategoryStats import CategoryStats


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewOut)
def stats_overview(request: Request):
    """
    Display statistics of the catalog:
    - total of books
    - average price
    - rating distribution   
    """
    books: List[Book] = request.app.state.books_cache

    total_books = len(books)
    average_price = round(
        sum(b.price for b in books) / total_books, 2
    ) if total_books else 0.0

    rating_counts = Counter(b.rating for b in books if 1 <= b.rating <= 5)
    ratings_distribution = {r: int(rating_counts.get(r, 0)) for r in range(1, 6)}

    return StatsOverviewOut(
        total_books=total_books,
        average_price=average_price,
        ratings_distribution=ratings_distribution,
    )


@router.get("/categories", response_model=StatsCategoriesOut)
def stats_categories(request: Request):
    """
    Display statistics by category:
    - Number of books
    - price (average, min, max) per category
    """
    books: List[Book] = request.app.state.books_cache

    by_cat = defaultdict(list)
    for b in books:
        by_cat[b.category].append(b.price)

    categories_stats: List[CategoryStats] = []
    for cat, prices in by_cat.items():
        n = len(prices)
        avg = round(sum(prices) / n, 2) if n else 0.0
        categories_stats.append(
            CategoryStats(
                category=cat,
                total_books=n,
                average_price=avg,
                min_price=round(min(prices), 2) if prices else 0.0,
                max_price=round(max(prices), 2) if prices else 0.0,
            )
        )

    categories_stats.sort(key=lambda x: (-x.total_books, x.category.lower()))

    return StatsCategoriesOut(
        total_categories=len(categories_stats),
        categories=categories_stats,
    )
