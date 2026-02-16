"""Cart router."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import CartItem, Product
from ..schemas import CartItemCreate, CartItemResponse, CartItemUpdate, CartResponse
from .expertise import remove_from_cart_internal, track_action_internal

router = APIRouter(prefix="/cart", tags=["cart"])


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required in X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("", response_model=CartResponse)
async def get_cart(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's cart."""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.reviews))
        .where(CartItem.user_id == user_id)
    )
    items = result.scalars().all()

    cart_items = []
    total_price = 0.0

    for item in items:
        cart_items.append(CartItemResponse(
            id=item.id,
            product=item.product,
            quantity=item.quantity
        ))
        total_price += item.product.price * item.quantity

    return CartResponse(
        items=cart_items,
        total_items=len(cart_items),
        total_price=round(total_price, 2)
    )


@router.post("/add", response_model=CartItemResponse)
async def add_to_cart(
    item_data: CartItemCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add item to cart (also tracks add_to_cart action)."""
    # Verify product exists
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.reviews))
        .where(Product.id == item_data.product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if item already in cart
    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == item_data.product_id
        )
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        # Update quantity
        existing_item.quantity += item_data.quantity
        await db.commit()
        await db.refresh(existing_item)
        cart_item = existing_item
    else:
        # Create new cart item
        cart_item = CartItem(
            user_id=user_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)

    # Track action for expertise
    await track_action_internal(db, user_id, "add_to_cart", item_data.product_id)

    return CartItemResponse(
        id=cart_item.id,
        product=product,
        quantity=cart_item.quantity
    )


@router.put("/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update cart item quantity."""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.reviews))
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if item_data.quantity <= 0:
        # Remove item if quantity is 0 or negative
        product_id = cart_item.product_id
        await db.delete(cart_item)
        await db.commit()
        # Also remove from expertise tracking
        await remove_from_cart_internal(db, user_id, product_id)
        raise HTTPException(status_code=200, detail="Item removed from cart")

    cart_item.quantity = item_data.quantity
    await db.commit()
    await db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        product=cart_item.product,
        quantity=cart_item.quantity
    )


@router.delete("/{item_id}")
async def remove_from_cart(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove item from cart (also removes from expertise tracking)."""
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user_id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    # Capture product_id before deletion
    product_id = cart_item.product_id

    await db.delete(cart_item)
    await db.commit()

    # Remove from expertise tracking
    await remove_from_cart_internal(db, user_id, product_id)

    return {"status": "success", "message": "Item removed from cart"}
