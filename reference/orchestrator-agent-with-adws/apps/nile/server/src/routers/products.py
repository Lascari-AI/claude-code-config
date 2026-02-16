"""Products router."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Product
from ..schemas import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductResponse])
async def list_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    shipping_speed: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all products with optional filters."""
    query = select(Product).options(selectinload(Product.reviews))

    if category:
        query = query.where(Product.category == category)
    if brand:
        query = query.where(Product.brand == brand)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if min_rating is not None:
        query = query.where(Product.rating >= min_rating)
    if shipping_speed:
        query = query.where(Product.shipping_speed == shipping_speed)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search products by name or description."""
    query = select(Product).options(selectinload(Product.reviews)).where(
        or_(
            Product.name.ilike(f"%{q}%"),
            Product.description.ilike(f"%{q}%"),
            Product.category.ilike(f"%{q}%"),
            Product.brand.ilike(f"%{q}%")
        )
    ).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/categories", response_model=List[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all product categories."""
    result = await db.execute(select(Product.category).distinct())
    return [row[0] for row in result.all()]


@router.get("/brands", response_model=List[str])
async def list_brands(db: AsyncSession = Depends(get_db)):
    """List all product brands."""
    result = await db.execute(select(Product.brand).distinct())
    return [row[0] for row in result.all()]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get product by ID."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.reviews))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get("/by-ids/{product_ids}", response_model=List[ProductResponse])
async def get_products_by_ids(
    product_ids: str,  # Comma-separated IDs
    db: AsyncSession = Depends(get_db)
):
    """Get multiple products by IDs (comma-separated)."""
    try:
        ids = [int(id.strip()) for id in product_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product IDs format")

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.reviews))
        .where(Product.id.in_(ids))
    )
    return result.scalars().all()
