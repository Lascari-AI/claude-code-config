"""Expertise router for Agent Expert learning."""
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Expertise
from ..schemas import ActionRequest, ExpertiseData, ExpertiseResponse
from ..services.agent_expert import ShoppingAgentExpert


class LiveSystemPromptResponse(BaseModel):
    """Response schema for the live system prompt."""
    system_prompt: str
    user_prompt: str
    total_improvements: int
    prefetched_products: dict


# Initialize agent expert for building prompts
_agent_expert: Optional[ShoppingAgentExpert] = None


def _get_agent_expert() -> ShoppingAgentExpert:
    """Lazy initialization of agent expert."""
    global _agent_expert
    if _agent_expert is None:
        _agent_expert = ShoppingAgentExpert()
    return _agent_expert

router = APIRouter(prefix="/expertise", tags=["expertise"])


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required in X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


async def get_or_create_expertise(db: AsyncSession, user_id: int) -> Expertise:
    """Get or create expertise record for user."""
    result = await db.execute(
        select(Expertise).where(Expertise.user_id == user_id)
    )
    expertise = result.scalar_one_or_none()

    if not expertise:
        expertise = Expertise(
            user_id=user_id,
            expertise_data={
                "viewed_products": [],
                "added_to_cart": [],
                "checked_out": []
            }
        )
        db.add(expertise)
        await db.commit()
        await db.refresh(expertise)

    return expertise


async def track_action_internal(
    db: AsyncSession,
    user_id: int,
    action_type: Literal["view_product_details", "add_to_cart", "checkout"],
    product_id: int
):
    """Internal function to track user actions (called by cart/orders routers)."""
    expertise = await get_or_create_expertise(db, user_id)

    now = datetime.utcnow().isoformat()
    data = expertise.expertise_data or {
        "viewed_products": [],
        "added_to_cart": [],
        "checked_out": []
    }

    # Map action type to data key
    action_map = {
        "view_product_details": ("viewed_products", "viewed_at", "view_count"),
        "add_to_cart": ("added_to_cart", "added_at", "add_count"),
        "checkout": ("checked_out", "checked_out_at", "purchase_count")
    }

    key, time_field, count_field = action_map[action_type]

    # Find existing entry for this product
    entries = data.get(key, [])
    existing = next((e for e in entries if e["product_id"] == product_id), None)

    if existing:
        # Update existing entry
        existing[time_field] = now
        existing[count_field] = existing.get(count_field, 0) + 1
    else:
        # Add new entry
        entries.append({
            "product_id": product_id,
            time_field: now,
            count_field: 1
        })

    data[key] = entries
    expertise.expertise_data = data
    expertise.total_improvements += 1
    expertise.last_improvement_at = datetime.utcnow()

    # Mark as modified for SQLAlchemy to detect JSON change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(expertise, "expertise_data")

    await db.commit()


async def remove_from_cart_internal(
    db: AsyncSession,
    user_id: int,
    product_id: int
):
    """Remove a product from the user's added_to_cart expertise when they remove it from cart.

    This keeps the expertise data in sync with actual cart state.
    """
    expertise = await get_or_create_expertise(db, user_id)

    data = expertise.expertise_data or {
        "viewed_products": [],
        "added_to_cart": [],
        "checked_out": []
    }

    # Find and remove the product from added_to_cart
    cart_entries = data.get("added_to_cart", [])
    original_count = len(cart_entries)
    cart_entries = [e for e in cart_entries if e.get("product_id") != product_id]

    if len(cart_entries) < original_count:
        # Item was found and removed
        data["added_to_cart"] = cart_entries
        expertise.expertise_data = data

        # Decrement total_improvements since we're undoing an action
        if expertise.total_improvements > 0:
            expertise.total_improvements -= 1

        # Mark as modified for SQLAlchemy to detect JSON change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(expertise, "expertise_data")

        await db.commit()


@router.get("", response_model=ExpertiseResponse)
async def get_expertise(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's expertise data."""
    expertise = await get_or_create_expertise(db, user_id)

    return ExpertiseResponse(
        id=expertise.id,
        user_id=expertise.user_id,
        total_improvements=expertise.total_improvements,
        last_improvement_at=expertise.last_improvement_at,
        expertise_data=ExpertiseData(**expertise.expertise_data)
    )


@router.post("/action")
async def track_action(
    action_data: ActionRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Track a user action (view, cart, checkout)."""
    await track_action_internal(db, user_id, action_data.action_type, action_data.product_id)

    expertise = await get_or_create_expertise(db, user_id)

    return {
        "status": "success",
        "action": action_data.action_type,
        "product_id": action_data.product_id,
        "total_improvements": expertise.total_improvements
    }


@router.delete("")
async def clear_expertise(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Clear user's expertise data (Cmd+C functionality)."""
    result = await db.execute(
        select(Expertise).where(Expertise.user_id == user_id)
    )
    expertise = result.scalar_one_or_none()

    if expertise:
        expertise.expertise_data = {
            "viewed_products": [],
            "added_to_cart": [],
            "checked_out": []
        }
        expertise.total_improvements = 0
        expertise.last_improvement_at = None

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(expertise, "expertise_data")

        await db.commit()

    return {"status": "success", "message": "Expertise cleared"}


@router.get("/live-prompt", response_model=LiveSystemPromptResponse)
async def get_live_system_prompt(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the live, populated system prompt as it would be sent to the agent.

    This endpoint builds the exact same system prompt that the agent receives,
    with all template variables populated from the user's expertise data.
    """
    expertise = await get_or_create_expertise(db, user_id)
    agent_expert = _get_agent_expert()

    # Pre-fetch user products
    prefetched_products = await agent_expert._prefetch_user_products(expertise, db)

    # Fetch all available categories and brands
    all_categories, all_brands = await agent_expert._fetch_all_categories_and_brands(db)

    # Build system prompt with populated variables (streaming version)
    system_prompt = agent_expert._build_streaming_system_prompt(
        expertise, prefetched_products, all_categories, all_brands
    )

    return LiveSystemPromptResponse(
        system_prompt=system_prompt,
        user_prompt=agent_expert.user_prompt_template,
        total_improvements=expertise.total_improvements,
        prefetched_products=prefetched_products
    )
