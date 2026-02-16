"""Product schemas."""
from typing import List, Optional

from pydantic import BaseModel


class ReviewResponse(BaseModel):
    """Schema for product review."""
    id: int
    review_text: str
    rating: int
    reviewer_name: str
    review_date: str

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str
    description: str
    price: float
    image_file_path: str
    category: str
    brand: str
    rating: float
    shipping_speed: str


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    name: str
    description: str
    price: float
    image_file_path: str
    category: str
    brand: str
    rating: float
    shipping_speed: str
    reviews: List[ReviewResponse] = []

    class Config:
        from_attributes = True


class ProductSearchParams(BaseModel):
    """Schema for product search parameters."""
    query: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    shipping_speed: Optional[str] = None
    limit: int = 20
    offset: int = 0
