import math
from typing import Any, Optional

from sqlalchemy import delete as sa_delete, func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.author import Author
from models.book import Book
from models.genre import Genre
from models.review import Review

BOOKS_PER_PAGE = 16


async def list_books(
    db: AsyncSession,
    search: Optional[str] = None,
    genre: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[int] = None,
    sort: Optional[str] = None,
    page: int = 1,
) -> dict[str, Any]:
    base_query = (
        select(
            Book,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.book_id == Book.id)
        .join(Author, Author.id == Book.author_id)
        .join(Genre, Genre.id == Book.genre_id)
        .group_by(Book.id)
    )

    count_query = select(func.count()).select_from(Book).join(Author, Author.id == Book.author_id).join(Genre, Genre.id == Book.genre_id)

    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(
            (Book.title.ilike(search_term)) | (Author.name.ilike(search_term))
        )
        count_query = count_query.where(
            (Book.title.ilike(search_term)) | (Author.name.ilike(search_term))
        )

    if genre is not None:
        base_query = base_query.where(Book.genre_id == genre)
        count_query = count_query.where(Book.genre_id == genre)

    if price_min is not None:
        base_query = base_query.where(Book.price >= price_min)
        count_query = count_query.where(Book.price >= price_min)

    if price_max is not None:
        base_query = base_query.where(Book.price <= price_max)
        count_query = count_query.where(Book.price <= price_max)

    if rating_min is not None:
        base_query = base_query.having(
            func.avg(Review.rating) >= rating_min
        )

    if sort == "price_asc":
        base_query = base_query.order_by(Book.price.asc())
    elif sort == "price_desc":
        base_query = base_query.order_by(Book.price.desc())
    elif sort == "rating":
        base_query = base_query.order_by(func.avg(Review.rating).desc().nulls_last())
    else:
        base_query = base_query.order_by(Book.created_at.desc())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    if rating_min is not None:
        total_pages = max(1, math.ceil(total / BOOKS_PER_PAGE))
    else:
        total_pages = max(1, math.ceil(total / BOOKS_PER_PAGE))

    if page < 1:
        page = 1

    offset = (page - 1) * BOOKS_PER_PAGE
    base_query = base_query.limit(BOOKS_PER_PAGE).offset(offset)

    result = await db.execute(base_query)
    rows = result.all()

    books = []
    for row in rows:
        book = row[0]
        avg_rating = row[1]
        rev_count = row[2]

        author_name = book.author.name if book.author else "Unknown"
        genre_name = book.genre.name if book.genre else "Unknown"

        books.append(
            {
                "id": book.id,
                "title": book.title,
                "author": author_name,
                "author_id": book.author_id,
                "genre": genre_name,
                "genre_id": book.genre_id,
                "price": book.price,
                "description": book.description,
                "isbn": book.isbn,
                "stock": book.stock,
                "publication_year": book.publication_year,
                "pages": book.pages,
                "average_rating": round(float(avg_rating), 1) if avg_rating is not None else None,
                "review_count": int(rev_count) if rev_count else 0,
                "created_at": book.created_at,
            }
        )

    if rating_min is not None:
        total = len(books) + offset
        total_pages = max(1, math.ceil(total / BOOKS_PER_PAGE)) if total > 0 else 1

    return {
        "books": books,
        "total": total,
        "page": page,
        "pages": total_pages,
    }


async def get_book_detail(db: AsyncSession, book_id: int) -> Optional[dict[str, Any]]:
    query = (
        select(
            Book,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.book_id == Book.id)
        .where(Book.id == book_id)
        .group_by(Book.id)
        .options(selectinload(Book.author), selectinload(Book.genre), selectinload(Book.reviews).selectinload(Review.user))
    )

    result = await db.execute(query)
    row = result.first()

    if row is None:
        return None

    book = row[0]
    avg_rating = row[1]
    rev_count = row[2]

    author_name = book.author.name if book.author else "Unknown"
    genre_name = book.genre.name if book.genre else "Unknown"

    reviews = []
    for review in book.reviews:
        reviews.append(
            {
                "id": review.id,
                "user": review.user.username if review.user else "Unknown",
                "user_id": review.user_id,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at,
            }
        )

    reviews.sort(key=lambda r: r["created_at"] if r["created_at"] else "", reverse=True)

    return {
        "id": book.id,
        "title": book.title,
        "author": author_name,
        "author_id": book.author_id,
        "genre": genre_name,
        "genre_id": book.genre_id,
        "price": book.price,
        "description": book.description,
        "isbn": book.isbn,
        "stock": book.stock,
        "publication_year": book.publication_year,
        "pages": book.pages,
        "average_rating": round(float(avg_rating), 1) if avg_rating is not None else None,
        "review_count": int(rev_count) if rev_count else 0,
        "reviews": reviews,
        "created_at": book.created_at,
    }


async def create_book(
    db: AsyncSession,
    title: str,
    author_id: int,
    genre_id: int,
    isbn: str,
    price: float,
    stock: int = 0,
    description: Optional[str] = None,
    publication_year: Optional[int] = None,
    pages: Optional[int] = None,
) -> Book:
    book = Book(
        title=title,
        author_id=author_id,
        genre_id=genre_id,
        isbn=isbn,
        price=price,
        stock=stock,
        description=description,
        publication_year=publication_year,
        pages=pages,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def update_book(
    db: AsyncSession,
    book_id: int,
    title: Optional[str] = None,
    author_id: Optional[int] = None,
    genre_id: Optional[int] = None,
    isbn: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[int] = None,
    description: Optional[str] = None,
    publication_year: Optional[int] = None,
    pages: Optional[int] = None,
) -> Optional[Book]:
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if book is None:
        return None

    if title is not None:
        book.title = title
    if author_id is not None:
        book.author_id = author_id
    if genre_id is not None:
        book.genre_id = genre_id
    if isbn is not None:
        book.isbn = isbn
    if price is not None:
        book.price = price
    if stock is not None:
        book.stock = stock
    if description is not None:
        book.description = description
    if publication_year is not None:
        book.publication_year = publication_year
    if pages is not None:
        book.pages = pages

    await db.flush()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> bool:
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if book is None:
        return False

    await db.delete(book)
    await db.flush()
    return True


async def get_book_by_id(db: AsyncSession, book_id: int) -> Optional[Book]:
    query = (
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.author), selectinload(Book.genre))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_authors(db: AsyncSession) -> list[dict[str, Any]]:
    query = (
        select(Author, func.count(Book.id).label("book_count"))
        .outerjoin(Book, Book.author_id == Author.id)
        .group_by(Author.id)
        .order_by(Author.name.asc())
    )
    result = await db.execute(query)
    rows = result.all()

    authors = []
    for row in rows:
        author = row[0]
        book_count = row[1]
        authors.append(
            {
                "id": author.id,
                "name": author.name,
                "bio": author.bio,
                "book_count": int(book_count) if book_count else 0,
                "created_at": author.created_at,
            }
        )
    return authors


async def get_author_by_id(db: AsyncSession, author_id: int) -> Optional[Author]:
    query = select(Author).where(Author.id == author_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_author(db: AsyncSession, name: str, bio: Optional[str] = None) -> Author:
    author = Author(name=name, bio=bio)
    db.add(author)
    await db.flush()
    await db.refresh(author)
    return author


async def update_author(
    db: AsyncSession, author_id: int, name: Optional[str] = None, bio: Optional[str] = None
) -> Optional[Author]:
    query = select(Author).where(Author.id == author_id)
    result = await db.execute(query)
    author = result.scalar_one_or_none()

    if author is None:
        return None

    if name is not None:
        author.name = name
    if bio is not None:
        author.bio = bio

    await db.flush()
    await db.refresh(author)
    return author


async def delete_author(db: AsyncSession, author_id: int) -> bool:
    query = select(Author).where(Author.id == author_id)
    result = await db.execute(query)
    author = result.scalar_one_or_none()

    if author is None:
        return False

    book_count_query = select(func.count(Book.id)).where(Book.author_id == author_id)
    book_count_result = await db.execute(book_count_query)
    book_count = book_count_result.scalar() or 0

    if book_count > 0:
        return False

    await db.delete(author)
    await db.flush()
    return True


async def list_genres(db: AsyncSession) -> list[dict[str, Any]]:
    query = (
        select(Genre, func.count(Book.id).label("book_count"))
        .outerjoin(Book, Book.genre_id == Genre.id)
        .group_by(Genre.id)
        .order_by(Genre.name.asc())
    )
    result = await db.execute(query)
    rows = result.all()

    genres = []
    for row in rows:
        genre = row[0]
        book_count = row[1]
        genres.append(
            {
                "id": genre.id,
                "name": genre.name,
                "book_count": int(book_count) if book_count else 0,
                "created_at": genre.created_at,
            }
        )
    return genres


async def get_genre_by_id(db: AsyncSession, genre_id: int) -> Optional[Genre]:
    query = select(Genre).where(Genre.id == genre_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_genre(db: AsyncSession, name: str) -> Genre:
    genre = Genre(name=name)
    db.add(genre)
    await db.flush()
    await db.refresh(genre)
    return genre


async def update_genre(db: AsyncSession, genre_id: int, name: Optional[str] = None) -> Optional[Genre]:
    query = select(Genre).where(Genre.id == genre_id)
    result = await db.execute(query)
    genre = result.scalar_one_or_none()

    if genre is None:
        return None

    if name is not None:
        genre.name = name

    await db.flush()
    await db.refresh(genre)
    return genre


async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
    query = select(Genre).where(Genre.id == genre_id)
    result = await db.execute(query)
    genre = result.scalar_one_or_none()

    if genre is None:
        return False

    book_count_query = select(func.count(Book.id)).where(Book.genre_id == genre_id)
    book_count_result = await db.execute(book_count_query)
    book_count = book_count_result.scalar() or 0

    if book_count > 0:
        return False

    await db.delete(genre)
    await db.flush()
    return True


async def get_low_stock_count(db: AsyncSession, threshold: int = 5) -> int:
    query = select(func.count(Book.id)).where(Book.stock <= threshold)
    result = await db.execute(query)
    return result.scalar() or 0


async def get_total_books_count(db: AsyncSession) -> int:
    query = select(func.count(Book.id))
    result = await db.execute(query)
    return result.scalar() or 0