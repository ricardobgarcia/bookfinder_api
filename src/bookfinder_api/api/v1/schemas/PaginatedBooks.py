from typing import List
from pydantic import BaseModel

from .BookOut import BookOut


class PaginatedBooks(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BookOut]
