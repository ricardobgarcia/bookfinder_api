from typing import List
from pydantic import BaseModel

from .CategoryStats import CategoryStats


class StatsCategoriesOut(BaseModel):
    total_categories: int
    categories: List[CategoryStats]
