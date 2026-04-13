import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.review import Review
from models.book import Book
from models.user import User


async def create_review(
    db: AsyncSession,
    user_id: int,
    book_id: int,
    rating: int,
    text: Optional[str] = None,
) -> Review:
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()
    if book is None:
        raise ValueError("Book not found")

    existing_result = await db.execute(
        select(Review).where(Review.user_id == user_id, Review.book_id == book_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        raise ValueError("You have already reviewed this book.")

    review = Review(
        user_id=user_id,
        book_id=book_id,
        rating=rating,
        text=text,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


async def get_book_reviews(
    db: AsyncSession,
    book_id: int,
) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.book_id == book_id)
        .options(selectinload(Review.user))
        .order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()
    return list(reviews)


async def get_review_by_id(
    db: AsyncSession,
    review_id: int,
) -> Optional[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.user), selectinload(Review.book))
    )
    return result.scalar_one_or_none()


async def update_review(
    db: AsyncSession,
    review_id: int,
    user_id: int,
    rating: Optional[int] = None,
    text: Optional[str] = None,
) -> Review:
    review = await get_review_by_id(db, review_id)
    if review is None:
        raise ValueError("Review not found")

    if review.user_id != user_id:
        raise PermissionError("You can only edit your own reviews.")

    if rating is not None:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        review.rating = rating

    if text is not None:
        review.text = text

    await db.flush()
    await db.refresh(review)
    return review


async def delete_review(
    db: AsyncSession,
    review_id: int,
    user_id: int,
    user_role: str = "customer",
) -> None:
    review = await get_review_by_id(db, review_id)
    if review is None:
        raise ValueError("Review not found")

    if review.user_id != user_id and user_role != "admin":
        raise PermissionError("You can only delete your own reviews.")

    await db.delete(review)
    await db.flush()


async def user_has_reviewed_book(
    db: AsyncSession,
    user_id: int,
    book_id: int,
) -> bool:
    result = await db.execute(
        select(Review).where(Review.user_id == user_id, Review.book_id == book_id)
    )
    return result.scalar_one_or_none() is not None


async def get_book_average_rating(
    db: AsyncSession,
    book_id: int,
) -> Optional[float]:
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.book_id == book_id)
    )
    avg = result.scalar_one_or_none()
    if avg is not None:
        return round(float(avg), 2)
    return None


async def get_book_review_count(
    db: AsyncSession,
    book_id: int,
) -> int:
    result = await db.execute(
        select(func.count(Review.id)).where(Review.book_id == book_id)
    )
    count = result.scalar_one_or_none()
    return count if count is not None else 0