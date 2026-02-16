"""Orders router."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import CartItem, OrderItem, Product
from ..schemas import OrderItemResponse, OrderResponse
from .expertise import track_action_internal

router = APIRouter(prefix="/orders", tags=["orders"])


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required in X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Checkout - convert cart to order (tracks checkout action for each item)."""
    # Get cart items
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.reviews))
        .where(CartItem.user_id == user_id)
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Create order items - truncate to seconds for consistent matching
    order_time = datetime.utcnow().replace(microsecond=0)
    order_id = f"ORD-{order_time.strftime('%Y%m%d%H%M%S')}-{user_id}"

    order_items = []
    total_price = 0.0

    for cart_item in cart_items:
        order_item = OrderItem(
            user_id=user_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.product.price,
            created_at=order_time
        )
        db.add(order_item)
        order_items.append(order_item)
        total_price += cart_item.product.price * cart_item.quantity

        # Track checkout action for each product
        await track_action_internal(db, user_id, "checkout", cart_item.product_id)

        # Remove from cart
        await db.delete(cart_item)

    await db.commit()

    # Refresh to get IDs
    for item in order_items:
        await db.refresh(item)

    # Build response with product details
    result = await db.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.product).selectinload(Product.reviews))
        .where(OrderItem.created_at == order_time, OrderItem.user_id == user_id)
    )
    order_items_with_products = result.scalars().all()

    return OrderResponse(
        order_id=order_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase,
                created_at=item.created_at
            )
            for item in order_items_with_products
        ],
        total_price=round(total_price, 2),
        created_at=order_time
    )


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all orders for user."""
    # Get distinct order timestamps
    result = await db.execute(
        select(OrderItem.created_at)
        .where(OrderItem.user_id == user_id)
        .distinct()
        .order_by(OrderItem.created_at.desc())
    )
    order_times = [row[0] for row in result.all()]

    orders = []
    for order_time in order_times:
        result = await db.execute(
            select(OrderItem)
            .options(selectinload(OrderItem.product).selectinload(Product.reviews))
            .where(OrderItem.user_id == user_id, OrderItem.created_at == order_time)
        )
        items = result.scalars().all()

        if items:
            total_price = sum(item.price_at_purchase * item.quantity for item in items)
            order_id = f"ORD-{order_time.strftime('%Y%m%d%H%M%S')}-{user_id}"

            orders.append(OrderResponse(
                order_id=order_id,
                items=[
                    OrderItemResponse(
                        id=item.id,
                        product=item.product,
                        quantity=item.quantity,
                        price_at_purchase=item.price_at_purchase,
                        created_at=item.created_at
                    )
                    for item in items
                ],
                total_price=round(total_price, 2),
                created_at=order_time
            ))

    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get specific order by ID."""
    # Parse order ID to get timestamp
    try:
        parts = order_id.split("-")
        timestamp_str = parts[1]
        order_time = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    result = await db.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.product).selectinload(Product.reviews))
        .where(OrderItem.user_id == user_id, OrderItem.created_at == order_time)
    )
    items = result.scalars().all()

    if not items:
        raise HTTPException(status_code=404, detail="Order not found")

    total_price = sum(item.price_at_purchase * item.quantity for item in items)

    return OrderResponse(
        order_id=order_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase,
                created_at=item.created_at
            )
            for item in items
        ],
        total_price=round(total_price, 2),
        created_at=order_time
    )
