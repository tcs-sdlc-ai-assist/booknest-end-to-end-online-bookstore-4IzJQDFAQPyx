import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.cart_service import (
    add_to_cart,
    get_cart,
    get_cart_count,
    remove_cart_item,
    update_cart_item,
)
from utils.dependencies import get_current_user, get_cart_count as get_cart_count_dep

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter()


@router.get("/cart")
async def cart_page(
    request: Request,
    user: User = Depends(get_current_user),
    cart_count: int = Depends(get_cart_count_dep),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, user.id)

    flash_messages = []
    success_msg = request.query_params.get("success")
    error_msg = request.query_params.get("error")
    if success_msg:
        flash_messages.append({"type": "success", "text": success_msg})
    if error_msg:
        flash_messages.append({"type": "error", "text": error_msg})

    return templates.TemplateResponse(
        request,
        "cart/index.html",
        context={
            "user": user,
            "cart": cart,
            "cart_count": cart_count,
            "flash_messages": flash_messages,
        },
    )


@router.post("/cart/add")
async def add_to_cart_route(
    request: Request,
    book_id: int = Form(...),
    quantity: int = Form(1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await add_to_cart(db, user.id, book_id, quantity)
        referer = request.headers.get("referer", "/cart")
        if "?" in referer:
            redirect_url = referer + "&success=Item added to cart."
        else:
            redirect_url = referer + "?success=Item added to cart."
        return RedirectResponse(url=redirect_url, status_code=303)
    except ValueError as e:
        referer = request.headers.get("referer", "/cart")
        error_text = str(e)
        if "?" in referer:
            redirect_url = referer + "&error=" + error_text
        else:
            redirect_url = referer + "?error=" + error_text
        return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/cart/{book_id}")
async def update_cart_item_route(
    book_id: int,
    quantity: int = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_cart_item(db, user.id, book_id, quantity)
        return RedirectResponse(url="/cart?success=Cart updated.", status_code=303)
    except ValueError as e:
        error_text = str(e)
        return RedirectResponse(url="/cart?error=" + error_text, status_code=303)


@router.post("/cart/{book_id}/remove")
async def remove_cart_item_route(
    book_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await remove_cart_item(db, user.id, book_id)
        return RedirectResponse(url="/cart?success=Item removed from cart.", status_code=303)
    except ValueError as e:
        error_text = str(e)
        return RedirectResponse(url="/cart?error=" + error_text, status_code=303)