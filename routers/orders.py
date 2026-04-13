import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.order_service import get_user_orders, get_order_detail
from utils.dependencies import get_current_user, get_cart_count

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/orders", response_class=HTMLResponse)
async def order_list(
    request: Request,
    page: int = 1,
    status_filter: Optional[str] = None,
    user: User = Depends(get_current_user),
    cart_count: int = Depends(get_cart_count),
    db: AsyncSession = Depends(get_db),
):
    status_param = request.query_params.get("status", None)
    if status_param:
        status_filter = status_param

    if page < 1:
        page = 1

    orders, total, pages = await get_user_orders(
        db=db,
        user_id=user.id,
        page=page,
        per_page=10,
        status_filter=status_filter if status_filter else None,
    )

    order_list_data = []
    for order in orders:
        order_list_data.append({
            "id": order.id,
            "total": order.total,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": order.order_items if order.order_items else [],
        })

    return templates.TemplateResponse(
        request,
        "orders/list.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "orders": order_list_data,
            "total": total,
            "page": page,
            "pages": pages,
            "status_filter": status_filter or "",
        },
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail_page(
    request: Request,
    order_id: int,
    user: User = Depends(get_current_user),
    cart_count: int = Depends(get_cart_count),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_detail(
        db=db,
        order_id=order_id,
        user_id=user.id,
        is_admin=False,
    )

    if order is None:
        return templates.TemplateResponse(
            request,
            "orders/list.html",
            context={
                "user": user,
                "cart_count": cart_count,
                "orders": [],
                "total": 0,
                "page": 1,
                "pages": 1,
                "status_filter": "",
                "error": "Order not found.",
            },
            status_code=404,
        )

    order_data = {
        "id": order.id,
        "total": order.total,
        "status": order.status,
        "shipping_address": order.shipping_address,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [],
    }

    for item in order.order_items:
        order_data["items"].append({
            "id": item.id,
            "book_id": item.book_id,
            "book_title": item.book_title,
            "quantity": item.quantity,
            "price": item.price,
        })

    return templates.TemplateResponse(
        request,
        "orders/detail.html",
        context={
            "user": user,
            "cart_count": cart_count,
            "order": order_data,
        },
    )