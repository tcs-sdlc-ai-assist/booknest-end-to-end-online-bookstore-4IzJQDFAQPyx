import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.cart_service import get_cart, get_cart_count
from services.order_service import check_stock_availability, create_order
from utils.dependencies import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/checkout")
async def checkout_page(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, user.id)
    cart_count = await get_cart_count(db, user.id)

    if not cart["items"]:
        return RedirectResponse(url="/cart", status_code=303)

    out_of_stock_items = await check_stock_availability(db, user.id)

    return templates.TemplateResponse(
        request,
        "checkout/index.html",
        context={
            "user": user,
            "cart": cart,
            "cart_count": cart_count,
            "out_of_stock_items": out_of_stock_items,
        },
    )


@router.post("/checkout")
async def checkout_submit(
    request: Request,
    street: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    country: str = Form("United States"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, user.id)
    cart_count = await get_cart_count(db, user.id)

    if not cart["items"]:
        return RedirectResponse(url="/cart", status_code=303)

    street = street.strip()
    city = city.strip()
    state = state.strip()
    zip_code = zip.strip()
    country = country.strip()

    errors = []
    if not street:
        errors.append("Street address is required.")
    if not city:
        errors.append("City is required.")
    if not state:
        errors.append("State is required.")
    if not zip_code:
        errors.append("ZIP code is required.")
    if not country:
        errors.append("Country is required.")

    if errors:
        out_of_stock_items = await check_stock_availability(db, user.id)
        return templates.TemplateResponse(
            request,
            "checkout/index.html",
            context={
                "user": user,
                "cart": cart,
                "cart_count": cart_count,
                "out_of_stock_items": out_of_stock_items,
                "error": " ".join(errors),
                "form_data": {
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": country,
                },
            },
        )

    out_of_stock_items = await check_stock_availability(db, user.id)
    if out_of_stock_items:
        return templates.TemplateResponse(
            request,
            "checkout/index.html",
            context={
                "user": user,
                "cart": cart,
                "cart_count": cart_count,
                "out_of_stock_items": out_of_stock_items,
                "form_data": {
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": country,
                },
            },
        )

    shipping_address = f"{street}\n{city}, {state} {zip_code}\n{country}"

    try:
        order = await create_order(
            db=db,
            user_id=user.id,
            shipping_address=shipping_address,
        )
    except ValueError as e:
        out_of_stock_items = await check_stock_availability(db, user.id)
        return templates.TemplateResponse(
            request,
            "checkout/index.html",
            context={
                "user": user,
                "cart": cart,
                "cart_count": cart_count,
                "out_of_stock_items": out_of_stock_items,
                "error": str(e),
                "form_data": {
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": country,
                },
            },
        )

    return RedirectResponse(url=f"/orders/{order.id}", status_code=303)