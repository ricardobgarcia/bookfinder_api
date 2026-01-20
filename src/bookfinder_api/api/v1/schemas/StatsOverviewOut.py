from typing import Dict, List
from pydantic import BaseModel, Field


class StatsOverviewOut(BaseModel):
    total_books: int
    average_price: float
    ratings_distribution: Dict[int, int] = Field(
        ..., description="Counts per rating (1..5)"
    )
