from typing import Dict, List
from pydantic import BaseModel, Field


class CategoryStats(BaseModel):
    category: str
    total_books: int
    average_price: float
    min_price: float
    max_price: float
    