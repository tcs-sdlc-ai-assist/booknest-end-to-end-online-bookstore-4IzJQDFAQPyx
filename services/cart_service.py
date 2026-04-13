from typing import Optional

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.cart_item import CartItem
from models.book import Book


async def get_cart(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.book))
    )
    cart_items = result.scalars().all()

    items = []
    total = 0.0
    item_count = 0

    for cart_item in cart_items:
        book = cart_item.book
        if book is None:
            continue
        subtotal = book.price * cart_item.quantity
        items.append({
            "id": cart_item.id,
            "book_id": book.id,
            "book_title": book.title,
            "book_price": book.price,
            "quantity": cart_item.quantity,
            "subtotal": round(subtotal, 2),
            "max_stock": book.stock,
        })
        total += subtotal
        item_count += cart_item.quantity

    return {
        "items": items,
        "total": round(total, 2),
        "item_count": item_count,
    }


async def add_to_cart(
    db: AsyncSession, user_id: int, book_id: int, quantity: int = 1
) -> dict:
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if book is None:
        raise ValueError("Book not found.")

    if book.stock <= 0:
        raise ValueError("This book is currently out of stock.")

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.book_id == book_id,
        )
    )
    existing_item = result.scalar_one_or_none()

    if existing_item is not None:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > book.stock:
            raise ValueError(
                f"Cannot add {quantity} more. Only {book.stock} available "
                f"(you already have {existing_item.quantity} in your cart)."
            )
        existing_item.quantity = new_quantity
        db.add(existing_item)
    else:
        if quantity > book.stock:
            raise ValueError(
                f"Cannot add {quantity}. Only {book.stock} available."
            )
        new_item = CartItem(
            user_id=user_id,
            book_id=book_id,
            quantity=quantity,
        )
        db.add(new_item)

    await db.flush()
    return {"message": "Item added to cart."}


async def update_cart_item(
    db: AsyncSession, user_id: int, book_id: int, quantity: int
) -> dict:
    result = await db.execute(
        select(CartItem)
        .where(
            CartItem.user_id == user_id,
            CartItem.book_id == book_id,
        )
        .options(selectinload(CartItem.book))
    )
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise ValueError("Item not found in cart.")

    book = cart_item.book
    if book is None:
        raise ValueError("Book not found.")

    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    if quantity > book.stock:
        raise ValueError(
            f"Cannot set quantity to {quantity}. Only {book.stock} available."
        )

    cart_item.quantity = quantity
    db.add(cart_item)
    await db.flush()
    return {"message": "Cart updated."}


async def remove_cart_item(
    db: AsyncSession, user_id: int, book_id: int
) -> dict:
    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.book_id == book_id,
        )
    )
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise ValueError("Item not found in cart.")

    await db.delete(cart_item)
    await db.flush()
    return {"message": "Item removed from cart."}


async def clear_cart(db: AsyncSession, user_id: int) -> dict:
    await db.execute(
        delete(CartItem).where(CartItem.user_id == user_id)
    )
    await db.flush()
    return {"message": "Cart cleared."}


async def get_cart_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(CartItem.quantity), 0)).where(
            CartItem.user_id == user_id
        )
    )
    count = result.scalar_one()
    return int(count)