import math
from typing import Optional, Tuple

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.book import Book
from models.cart_item import CartItem
from models.order import Order, OrderItem
from models.user import User


async def create_order(
    db: AsyncSession,
    user_id: int,
    shipping_address: str,
) -> Order:
    cart_result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.book))
    )
    cart_items = cart_result.scalars().all()

    if not cart_items:
        raise ValueError("Cart is empty.")

    out_of_stock = []
    for item in cart_items:
        book = item.book
        if book is None:
            out_of_stock.append({
                "book_title": "Unknown",
                "quantity": item.quantity,
                "available": 0,
            })
        elif book.stock < item.quantity:
            out_of_stock.append({
                "book_title": book.title,
                "quantity": item.quantity,
                "available": book.stock,
            })

    if out_of_stock:
        raise ValueError(f"Out of stock items: {out_of_stock}")

    total = 0.0
    order = Order(
        user_id=user_id,
        total=0.0,
        status="pending",
        shipping_address=shipping_address,
    )
    db.add(order)
    await db.flush()

    for item in cart_items:
        book = item.book
        price_at_purchase = book.price
        subtotal = price_at_purchase * item.quantity
        total += subtotal

        order_item = OrderItem(
            order_id=order.id,
            book_id=book.id,
            book_title=book.title,
            quantity=item.quantity,
            price=price_at_purchase,
        )
        db.add(order_item)

        book.stock -= item.quantity

    order.total = round(total, 2)

    await db.execute(
        delete(CartItem).where(CartItem.user_id == user_id)
    )

    await db.flush()

    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.order_items))
    )
    order = result.scalar_one()

    return order


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
    status_filter: Optional[str] = None,
) -> Tuple[list, int, int]:
    query = select(Order).where(Order.user_id == user_id)

    if status_filter:
        query = query.where(Order.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, pages))
    offset = (page - 1) * per_page

    query = (
        query
        .options(selectinload(Order.order_items))
        .order_by(Order.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )

    result = await db.execute(query)
    orders = result.scalars().all()

    return list(orders), total, pages


async def get_order_detail(
    db: AsyncSession,
    order_id: int,
    user_id: int,
    is_admin: bool = False,
) -> Optional[Order]:
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.order_items))
    )

    if not is_admin:
        query = query.where(Order.user_id == user_id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()

    return order


async def get_all_orders(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
) -> Tuple[list, int, int]:
    query = select(Order)

    if status_filter:
        query = query.where(Order.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, pages))
    offset = (page - 1) * per_page

    query = (
        query
        .options(
            selectinload(Order.order_items),
            selectinload(Order.user),
        )
        .order_by(Order.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )

    result = await db.execute(query)
    orders = result.scalars().all()

    return list(orders), total, pages


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    new_status: str,
) -> Optional[Order]:
    valid_statuses = {"pending", "processing", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.order_items))
    )
    order = result.scalar_one_or_none()

    if order is None:
        return None

    order.status = new_status
    await db.flush()

    return order


async def check_stock_availability(
    db: AsyncSession,
    user_id: int,
) -> list:
    cart_result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.book))
    )
    cart_items = cart_result.scalars().all()

    out_of_stock = []
    for item in cart_items:
        book = item.book
        if book is None or book.stock < item.quantity:
            out_of_stock.append({
                "book_title": book.title if book else "Unknown",
                "quantity": item.quantity,
                "available": book.stock if book else 0,
            })

    return out_of_stock