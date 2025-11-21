from dataclasses import dataclass
from pydantic import BaseModel
from typing import List


@dataclass
class Book:
    title: str
    price: float
    rating: int
    availability: str
    category: str
    image_url: str
