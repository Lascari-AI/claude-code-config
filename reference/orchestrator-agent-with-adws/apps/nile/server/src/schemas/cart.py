"""Cart schemas."""
from typing import List

from pydantic import BaseModel

from .product import ProductResponse


class CartItemCreate(BaseModel):
    """Schema for adding item to cart."""
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Schema for updating cart item."""
    quantity: int


class CartItemResponse(BaseModel):
    """Schema for cart item response."""
    id: int
    product: ProductResponse
    quantity: int

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    """Schema for full cart response."""
    items: List[CartItemResponse]
    total_items: int
    total_price: float
