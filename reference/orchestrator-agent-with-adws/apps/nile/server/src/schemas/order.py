"""Order schemas."""
from datetime import datetime
from typing import List

from pydantic import BaseModel

from .product import ProductResponse


class OrderCreate(BaseModel):
    """Schema for creating an order (checkout)."""
    pass  # Items come from cart


class OrderItemResponse(BaseModel):
    """Schema for order item response."""
    id: int
    product: ProductResponse
    quantity: int
    price_at_purchase: float
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response."""
    order_id: str  # Group of order items with same timestamp
    items: List[OrderItemResponse]
    total_price: float
    created_at: datetime
