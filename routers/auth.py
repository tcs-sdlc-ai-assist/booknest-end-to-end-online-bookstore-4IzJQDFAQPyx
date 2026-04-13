import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth_service import authenticate_user, create_jwt, register_user
from utils.dependencies import get_optional_user, get_cart_count
from models.user import User

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/register")
async def register_page(
    request: Request,
    user=Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is not None:
        return RedirectResponse(url="/books", status_code=302)

    return templates.TemplateResponse(
        request,
        "auth/register.html",
        context={
            "user": user,
            "cart_count": cart_count,
        },
    )


@router.post("/register")
async def register_submit(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is not None:
        return RedirectResponse(url="/books", status_code=302)

    errors = []
    form_data = {
        "display_name": display_name,
        "email": email,
        "username": username,
    }

    display_name = display_name.strip()
    username = username.strip()
    email = email.strip()

    if not display_name:
        errors.append("Display name is required.")

    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters long.")
    elif len(username) > 50:
        errors.append("Username must be at most 50 characters long.")
    elif not all(c.isalnum() or c in ("_", "-") for c in username):
        errors.append("Username may only contain letters, digits, hyphens, and underscores.")

    if not email:
        errors.append("Email is required.")

    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            context={
                "errors": errors,
                "form_data": form_data,
                "user": None,
                "cart_count": 0,
            },
        )

    try:
        await register_user(
            db=db,
            display_name=display_name,
            email=email,
            username=username,
            password=password,
        )
    except ValueError as e:
        errors.append(str(e))
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            context={
                "errors": errors,
                "form_data": form_data,
                "user": None,
                "cart_count": 0,
            },
        )

    response = RedirectResponse(url="/login", status_code=302)
    return response


@router.get("/login")
async def login_page(
    request: Request,
    user=Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is not None:
        return RedirectResponse(url="/books", status_code=302)

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        context={
            "user": user,
            "cart_count": cart_count,
        },
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
    cart_count: int = Depends(get_cart_count),
):
    if user is not None:
        return RedirectResponse(url="/books", status_code=302)

    username = username.strip()

    if not username or not password:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            context={
                "error": "Username and password are required.",
                "username": username,
                "user": None,
                "cart_count": 0,
            },
        )

    authenticated_user = await authenticate_user(db=db, username=username, password=password)

    if authenticated_user is None:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            context={
                "error": "Invalid username or password.",
                "username": username,
                "user": None,
                "cart_count": 0,
            },
        )

    token = create_jwt(authenticated_user)

    if authenticated_user.role == "admin":
        redirect_url = "/admin"
    else:
        redirect_url = "/books"

    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60,
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@router.post("/logout")
async def logout_post(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response