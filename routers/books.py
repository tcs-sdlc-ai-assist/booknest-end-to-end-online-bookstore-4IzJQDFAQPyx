import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.book_service import get_book_detail, list_books, list_genres
from services.review_service import (
    create_review,
    delete_review,
    get_book_reviews,
    update_review,
    user_has_reviewed_book,
)
from utils.dependencies import get_cart_count, get_optional_user

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/books")
async def catalog_page(
    request: Request,
    search: Optional[str] = Query(default=None),
    genre: Optional[int] = Query(default=None),
    price_min: Optional[float] = Query(default=None),
    price_max: Optional[float] = Query(default=None),
    rating_min: Optional[int] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    result = await list_books(
        db=db,
        search=search,
        genre=genre,
        price_min=price_min,
        price_max=price_max,
        rating_min=rating_min,
        sort=sort,
        page=page,
    )

    genres = await list_genres(db)

    flash_messages = []

    return templates.TemplateResponse(
        request,
        "books/catalog.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "books": result["books"],
            "total": result["total"],
            "page": result["page"],
            "pages": result["pages"],
            "genres": genres,
            "search": search or "",
            "genre": genre,
            "price_min": price_min,
            "price_max": price_max,
            "rating_min": rating_min,
            "sort": sort or "newest",
            "flash_messages": flash_messages,
        },
    )


@router.get("/books/{book_id}")
async def book_detail_page(
    request: Request,
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    book = await get_book_detail(db, book_id)

    if book is None:
        return templates.TemplateResponse(
            request,
            "books/catalog.html",
            context={
                "user": user,
                "cart_count": cart_count,
                "books": [],
                "total": 0,
                "page": 1,
                "pages": 1,
                "genres": [],
                "search": "",
                "genre": None,
                "price_min": None,
                "price_max": None,
                "rating_min": None,
                "sort": "newest",
                "flash_messages": [{"type": "error", "text": "Book not found."}],
                "error": "Book not found.",
            },
            status_code=404,
        )

    has_reviewed = False
    if user is not None:
        has_reviewed = await user_has_reviewed_book(db, user.id, book_id)

    flash_messages = []

    return templates.TemplateResponse(
        request,
        "books/detail.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "book": book,
            "user_has_reviewed": has_reviewed,
            "flash_messages": flash_messages,
        },
    )


@router.post("/books/{book_id}/reviews")
async def create_book_review(
    request: Request,
    book_id: int,
    rating: int = Form(...),
    text: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    try:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        if text is not None and len(text.strip()) == 0:
            text = None

        if text is not None and len(text) > 1000:
            raise ValueError("Review text must be at most 1000 characters.")

        await create_review(
            db=db,
            user_id=user.id,
            book_id=book_id,
            rating=rating,
            text=text,
        )

        return RedirectResponse(url=f"/books/{book_id}", status_code=303)

    except ValueError as e:
        book = await get_book_detail(db, book_id)
        if book is None:
            return RedirectResponse(url="/books", status_code=303)

        has_reviewed = await user_has_reviewed_book(db, user.id, book_id)

        return templates.TemplateResponse(
            request,
            "books/detail.html",
            context={
                "user": user,
                "cart_count": cart_count,
                "book": book,
                "user_has_reviewed": has_reviewed,
                "error": str(e),
                "flash_messages": [{"type": "error", "text": str(e)}],
            },
            status_code=400,
        )


@router.post("/books/{book_id}/reviews/{review_id}/edit")
async def edit_book_review(
    request: Request,
    book_id: int,
    review_id: int,
    rating: int = Form(...),
    text: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    try:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        if text is not None and len(text.strip()) == 0:
            text = None

        if text is not None and len(text) > 1000:
            raise ValueError("Review text must be at most 1000 characters.")

        await update_review(
            db=db,
            review_id=review_id,
            user_id=user.id,
            rating=rating,
            text=text,
        )

        return RedirectResponse(url=f"/books/{book_id}", status_code=303)

    except (ValueError, PermissionError) as e:
        book = await get_book_detail(db, book_id)
        if book is None:
            return RedirectResponse(url="/books", status_code=303)

        has_reviewed = await user_has_reviewed_book(db, user.id, book_id)

        return templates.TemplateResponse(
            request,
            "books/detail.html",
            context={
                "user": user,
                "cart_count": cart_count,
                "book": book,
                "user_has_reviewed": has_reviewed,
                "error": str(e),
                "flash_messages": [{"type": "error", "text": str(e)}],
            },
            status_code=400,
        )


@router.post("/books/{book_id}/reviews/{review_id}/delete")
async def delete_book_review(
    request: Request,
    book_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    try:
        await delete_review(
            db=db,
            review_id=review_id,
            user_id=user.id,
            user_role=user.role,
        )

        return RedirectResponse(url=f"/books/{book_id}", status_code=303)

    except (ValueError, PermissionError) as e:
        book = await get_book_detail(db, book_id)
        if book is None:
            return RedirectResponse(url="/books", status_code=303)

        has_reviewed = await user_has_reviewed_book(db, user.id, book_id)

        return templates.TemplateResponse(
            request,
            "books/detail.html",
            context={
                "user": user,
                "cart_count": cart_count,
                "book": book,
                "user_has_reviewed": has_reviewed,
                "error": str(e),
                "flash_messages": [{"type": "error", "text": str(e)}],
            },
            status_code=400,
        )