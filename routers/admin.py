import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.order import Order
from models.user import User
from services.book_service import (
    create_author,
    create_book,
    create_genre,
    delete_author,
    delete_book,
    delete_genre,
    get_low_stock_count,
    get_total_books_count,
    list_authors,
    list_books,
    list_genres,
    update_author,
    update_book,
    update_genre,
)
from services.order_service import get_all_orders, update_order_status
from utils.dependencies import get_cart_count, get_current_admin

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/admin")
async def admin_dashboard(
    request: Request,
    tab: Optional[str] = Query(default=None),
    book_search: Optional[str] = Query(default=None),
    genre_filter: Optional[str] = Query(default=None),
    books_page: int = Query(default=1),
    order_status: Optional[str] = Query(default=None),
    orders_page: int = Query(default=1),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    total_books = await get_total_books_count(db)

    count_result = await db.execute(select(func.count(Order.id)))
    total_orders = count_result.scalar() or 0

    revenue_result = await db.execute(select(func.coalesce(func.sum(Order.total), 0.0)))
    total_revenue = revenue_result.scalar() or 0.0

    low_stock_count = await get_low_stock_count(db)

    genre_id = None
    if genre_filter and genre_filter.strip():
        try:
            genre_id = int(genre_filter)
        except (ValueError, TypeError):
            genre_id = None

    books_result = await list_books(
        db,
        search=book_search if book_search else None,
        genre=genre_id,
        page=books_page,
    )
    books = books_result["books"]
    books_total = books_result["total"]
    books_pages = books_result["pages"]

    authors = await list_authors(db)
    genres = await list_genres(db)

    status_filter = order_status if order_status and order_status.strip() else None
    orders_list, orders_total, orders_pages = await get_all_orders(
        db,
        page=orders_page,
        per_page=20,
        status_filter=status_filter,
    )

    orders = []
    for order in orders_list:
        customer_name = ""
        if order.user:
            customer_name = order.user.display_name or order.user.username
        orders.append({
            "id": order.id,
            "customer": customer_name,
            "total": order.total,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at,
            "updated_at": getattr(order, "updated_at", None),
        })

    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "total_books": total_books,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "low_stock_count": low_stock_count,
            "books": books,
            "books_total": books_total,
            "books_page": books_page,
            "books_pages": books_pages,
            "book_search": book_search or "",
            "genre_filter": genre_filter or "",
            "authors": authors,
            "genres": genres,
            "orders": orders,
            "orders_total": orders_total,
            "orders_page": orders_page,
            "orders_pages": orders_pages,
            "order_status": order_status or "",
            "tab": tab or "books",
        },
    )


@router.post("/admin/books/add")
async def admin_add_book(
    request: Request,
    title: str = Form(...),
    author_id: int = Form(...),
    genre_id: int = Form(...),
    isbn: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    publication_year: Optional[str] = Form(default=None),
    pages: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    pub_year = None
    if publication_year and publication_year.strip():
        try:
            pub_year = int(publication_year)
        except (ValueError, TypeError):
            pub_year = None

    pages_int = None
    if pages and pages.strip():
        try:
            pages_int = int(pages)
        except (ValueError, TypeError):
            pages_int = None

    try:
        await create_book(
            db,
            title=title.strip(),
            author_id=author_id,
            genre_id=genre_id,
            isbn=isbn.strip(),
            price=price,
            stock=stock,
            description=description.strip() if description else None,
            publication_year=pub_year,
            pages=pages_int,
        )
    except Exception:
        return RedirectResponse(url="/admin?tab=books", status_code=303)

    return RedirectResponse(url="/admin?tab=books", status_code=303)


@router.get("/admin/books/create")
async def admin_book_create_form(
    request: Request,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    authors = await list_authors(db)
    genres = await list_genres(db)

    return templates.TemplateResponse(
        request,
        "admin/book_form.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "book": None,
            "authors": authors,
            "genres": genres,
        },
    )


@router.post("/admin/books/create")
async def admin_book_create_submit(
    request: Request,
    title: str = Form(...),
    author_id: int = Form(...),
    genre_id: int = Form(...),
    isbn: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    publication_year: Optional[str] = Form(default=None),
    pages: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    pub_year = None
    if publication_year and publication_year.strip():
        try:
            pub_year = int(publication_year)
        except (ValueError, TypeError):
            pub_year = None

    pages_int = None
    if pages and pages.strip():
        try:
            pages_int = int(pages)
        except (ValueError, TypeError):
            pages_int = None

    try:
        await create_book(
            db,
            title=title.strip(),
            author_id=author_id,
            genre_id=genre_id,
            isbn=isbn.strip(),
            price=price,
            stock=stock,
            description=description.strip() if description else None,
            publication_year=pub_year,
            pages=pages_int,
        )
    except Exception:
        authors = await list_authors(db)
        genres = await list_genres(db)
        return templates.TemplateResponse(
            request,
            "admin/book_form.html",
            context={
                "user": user,
                "cart_count": 0,
                "book": None,
                "authors": authors,
                "genres": genres,
                "error": "Failed to create book. Please check the details and try again.",
            },
        )

    return RedirectResponse(url="/admin?tab=books", status_code=303)


@router.get("/admin/books/{book_id}/edit")
async def admin_book_edit_form(
    request: Request,
    book_id: int,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    from services.book_service import get_book_by_id

    book = await get_book_by_id(db, book_id)
    if book is None:
        return RedirectResponse(url="/admin?tab=books", status_code=303)

    authors = await list_authors(db)
    genres = await list_genres(db)

    return templates.TemplateResponse(
        request,
        "admin/book_form.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "book": book,
            "authors": authors,
            "genres": genres,
        },
    )


@router.post("/admin/books/{book_id}/edit")
async def admin_book_edit_submit(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author_id: int = Form(...),
    genre_id: int = Form(...),
    isbn: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    publication_year: Optional[str] = Form(default=None),
    pages: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    pub_year = None
    if publication_year and publication_year.strip():
        try:
            pub_year = int(publication_year)
        except (ValueError, TypeError):
            pub_year = None

    pages_int = None
    if pages and pages.strip():
        try:
            pages_int = int(pages)
        except (ValueError, TypeError):
            pages_int = None

    try:
        await update_book(
            db,
            book_id=book_id,
            title=title.strip(),
            author_id=author_id,
            genre_id=genre_id,
            isbn=isbn.strip(),
            price=price,
            stock=stock,
            description=description.strip() if description else None,
            publication_year=pub_year,
            pages=pages_int,
        )
    except Exception:
        return RedirectResponse(url=f"/admin/books/{book_id}/edit", status_code=303)

    return RedirectResponse(url="/admin?tab=books", status_code=303)


@router.post("/admin/books/{book_id}/delete")
async def admin_book_delete(
    request: Request,
    book_id: int,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_book(db, book_id)
    return RedirectResponse(url="/admin?tab=books", status_code=303)


@router.get("/admin/authors")
async def admin_authors_page(
    request: Request,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    authors = await list_authors(db)

    return templates.TemplateResponse(
        request,
        "admin/authors.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "authors": authors,
        },
    )


@router.post("/admin/authors")
async def admin_authors_create(
    request: Request,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await create_author(db, name=name.strip())
    except Exception:
        pass
    return RedirectResponse(url="/admin/authors", status_code=303)


@router.post("/admin/authors/add")
async def admin_authors_add_inline(
    request: Request,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await create_author(db, name=name.strip())
    except Exception:
        pass
    return RedirectResponse(url="/admin?tab=authors", status_code=303)


@router.post("/admin/authors/{author_id}/edit")
async def admin_author_edit(
    request: Request,
    author_id: int,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_author(db, author_id=author_id, name=name.strip())
    except Exception:
        pass

    referer = request.headers.get("referer", "")
    if "/admin/authors" in referer:
        return RedirectResponse(url="/admin/authors", status_code=303)
    return RedirectResponse(url="/admin?tab=authors", status_code=303)


@router.post("/admin/authors/{author_id}/delete")
async def admin_author_delete(
    request: Request,
    author_id: int,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_author(db, author_id)

    referer = request.headers.get("referer", "")
    if "/admin/authors" in referer:
        return RedirectResponse(url="/admin/authors", status_code=303)
    return RedirectResponse(url="/admin?tab=authors", status_code=303)


@router.get("/admin/genres")
async def admin_genres_page(
    request: Request,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    genres = await list_genres(db)

    return templates.TemplateResponse(
        request,
        "admin/genres.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "genres": genres,
        },
    )


@router.post("/admin/genres")
async def admin_genres_create(
    request: Request,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await create_genre(db, name=name.strip())
    except Exception:
        pass
    return RedirectResponse(url="/admin/genres", status_code=303)


@router.post("/admin/genres/add")
async def admin_genres_add_inline(
    request: Request,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await create_genre(db, name=name.strip())
    except Exception:
        pass
    return RedirectResponse(url="/admin?tab=genres", status_code=303)


@router.post("/admin/genres/{genre_id}/edit")
async def admin_genre_edit(
    request: Request,
    genre_id: int,
    name: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_genre(db, genre_id=genre_id, name=name.strip())
    except Exception:
        pass

    referer = request.headers.get("referer", "")
    if "/admin/genres" in referer:
        return RedirectResponse(url="/admin/genres", status_code=303)
    return RedirectResponse(url="/admin?tab=genres", status_code=303)


@router.post("/admin/genres/{genre_id}/delete")
async def admin_genre_delete(
    request: Request,
    genre_id: int,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_genre(db, genre_id)

    referer = request.headers.get("referer", "")
    if "/admin/genres" in referer:
        return RedirectResponse(url="/admin/genres", status_code=303)
    return RedirectResponse(url="/admin?tab=genres", status_code=303)


@router.get("/admin/orders")
async def admin_orders_page(
    request: Request,
    page: int = Query(default=1),
    status: Optional[str] = Query(default=None),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    cart_count: int = Depends(get_cart_count),
):
    status_filter = status if status and status.strip() else None

    orders_list, total, pages = await get_all_orders(
        db,
        page=page,
        per_page=20,
        status_filter=status_filter,
    )

    orders = []
    for order in orders_list:
        customer_name = ""
        customer_username = ""
        if order.user:
            customer_name = order.user.display_name or ""
            customer_username = order.user.username or ""

        item_count = len(order.order_items) if order.order_items else 0

        orders.append({
            "id": order.id,
            "customer_name": customer_name,
            "customer_username": customer_username,
            "total": order.total,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at,
            "updated_at": getattr(order, "updated_at", None),
            "item_count": item_count,
        })

    filters = {"status": status_filter or ""}

    return templates.TemplateResponse(
        request,
        "admin/orders.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "orders": orders,
            "total": total,
            "page": page,
            "pages": pages,
            "filters": filters,
        },
    )


@router.post("/admin/orders/{order_id}/status")
async def admin_order_update_status(
    request: Request,
    order_id: int,
    status: str = Form(...),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_order_status(db, order_id=order_id, new_status=status.strip())
    except (ValueError, Exception):
        pass

    referer = request.headers.get("referer", "")
    if "/admin/orders" in referer and "/admin/orders/" not in referer:
        return RedirectResponse(url="/admin/orders", status_code=303)
    if "/admin?" in referer or referer.endswith("/admin"):
        return RedirectResponse(url="/admin?tab=orders", status_code=303)
    return RedirectResponse(url="/admin?tab=orders", status_code=303)