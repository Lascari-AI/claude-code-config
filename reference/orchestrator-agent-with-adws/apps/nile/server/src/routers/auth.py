"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Login or create user by name (no password for demo)."""
    # Find existing user
    result = await db.execute(
        select(User).where(User.name == user_data.name)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(name=user_data.name)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
