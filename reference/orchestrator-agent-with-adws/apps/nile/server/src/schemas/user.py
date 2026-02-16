"""User schemas."""
from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema for creating a user."""
    name: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """Schema for user in database."""
    updated_at: datetime
