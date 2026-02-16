"""Expertise schemas for Agent Expert."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class ViewedProduct(BaseModel):
    """Schema for viewed product entry."""
    product_id: int
    viewed_at: str
    view_count: int = 1


class AddedToCart(BaseModel):
    """Schema for added to cart entry."""
    product_id: int
    added_at: str
    add_count: int = 1


class CheckedOut(BaseModel):
    """Schema for checked out entry."""
    product_id: int
    checked_out_at: str
    purchase_count: int = 1


class ExpertiseData(BaseModel):
    """Schema for expertise data structure."""
    viewed_products: List[ViewedProduct] = []
    added_to_cart: List[AddedToCart] = []
    checked_out: List[CheckedOut] = []


class ExpertiseResponse(BaseModel):
    """Schema for expertise response."""
    id: int
    user_id: int
    total_improvements: int
    last_improvement_at: Optional[datetime]
    expertise_data: ExpertiseData

    class Config:
        from_attributes = True


class ActionRequest(BaseModel):
    """Schema for tracking user actions."""
    action_type: Literal["view_product_details", "add_to_cart", "checkout"]
    product_id: int
