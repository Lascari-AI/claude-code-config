"""Home page router with Agent Expert integration."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Expertise, Product
from ..schemas import HomePageResponse, HomeSection, ProductResponse

router = APIRouter(prefix="/home", tags=["home"])


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required in X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


async def get_random_products(db: AsyncSession, limit: int = 8) -> list:
    """Get random products from database."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.reviews))
        .order_by(func.random())
        .limit(limit)
    )
    return result.scalars().all()


async def generate_generic_home(db: AsyncSession) -> HomePageResponse:
    """Generate generic home page for new users."""
    # Get random products for different sections
    hero_products = await get_random_products(db, 6)
    featured_products = await get_random_products(db, 8)

    sections = [
        HomeSection(
            component_type="generic-slogan",
            slogan_text="Welcome to Nile - Where Every Purchase Flows Smoothly",
            subtitle="Discover premium products curated just for you"
        ),
        HomeSection(
            component_type="carousel",
            title="Featured Products",
            products=[ProductResponse.model_validate(p) for p in hero_products[:6]]
        ),
        HomeSection(
            component_type="basic-square",
            title="Popular Categories",
            products=[ProductResponse.model_validate(p) for p in featured_products[:4]]
        ),
        HomeSection(
            component_type="card",
            title="New Arrivals",
            products=[ProductResponse.model_validate(p) for p in featured_products[4:8]]
        )
    ]

    return HomePageResponse(sections=sections, is_personalized=False)


@router.get("", response_model=HomePageResponse)
async def get_home_page(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get home page - returns generic content. Use WebSocket streaming for personalized content."""
    # HTTP endpoint returns generic home page
    # Personalized content is delivered via WebSocket streaming (/ws/home/{user_id})
    return await generate_generic_home(db)


@router.get("/autocomplete")
async def get_search_autocomplete(
    q: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized search autocomplete suggestions."""
    # Get expertise for personalization
    result = await db.execute(
        select(Expertise).where(Expertise.user_id == user_id)
    )
    expertise = result.scalar_one_or_none()

    # Get matching products
    result = await db.execute(
        select(Product)
        .where(
            (Product.name.ilike(f"%{q}%")) |
            (Product.category.ilike(f"%{q}%")) |
            (Product.brand.ilike(f"%{q}%"))
        )
        .limit(10)
    )
    products = result.scalars().all()

    suggestions = []

    # If user has expertise, prioritize relevant products
    if expertise and expertise.expertise_data:
        viewed_ids = {e["product_id"] for e in expertise.expertise_data.get("viewed_products", [])}
        carted_ids = {e["product_id"] for e in expertise.expertise_data.get("added_to_cart", [])}

        # Score products based on expertise
        scored = []
        for p in products:
            score = 0
            if p.id in carted_ids:
                score += 2
            if p.id in viewed_ids:
                score += 1
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        products = [p for _, p in scored]

    for p in products[:5]:
        suggestions.append({
            "text": p.name,
            "product_id": p.id,
            "category": p.category
        })

    return {"suggestions": suggestions, "query": q}
