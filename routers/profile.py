import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.order_service import get_user_orders
from utils.dependencies import get_current_user, get_cart_count

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/profile")
async def profile_page(
    request: Request,
    user: User = Depends(get_current_user),
    cart_count: int = Depends(get_cart_count),
    db: AsyncSession = Depends(get_db),
):
    recent_orders, total_orders, total_pages = await get_user_orders(
        db=db,
        user_id=user.id,
        page=1,
        per_page=5,
    )

    order_list = []
    for order in recent_orders:
        order_list.append({
            "id": order.id,
            "total": order.total,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "items": order.order_items,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        })

    profile_data = {
        "id": user.id,
        "display_name": user.display_name,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at,
    }

    return templates.TemplateResponse(
        request,
        "profile/index.html",
        context={
            "user": user,
            "profile": profile_data,
            "recent_orders": order_list,
            "cart_count": cart_count,
        },
    )