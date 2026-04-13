import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, get_db
from main import app
from models.user import User
from utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_register_page_loads(client: AsyncClient):
    response = await client.get("/register")
    assert response.status_code == 200
    assert "Create your account" in response.text


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/register",
        data={
            "display_name": "New User",
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    result = await db_session.execute(select(User).where(User.username == "newuser"))
    user = result.scalars().first()
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.display_name == "New User"
    assert user.role == "customer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/register",
        data={
            "display_name": "Another User",
            "email": customer_user.email,
            "username": "anotheruser",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Email already exists" in response.text


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/register",
        data={
            "display_name": "Another User",
            "email": "unique@example.com",
            "username": customer_user.username,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Username already exists" in response.text


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    response = await client.post(
        "/register",
        data={
            "display_name": "Short Pass",
            "email": "shortpass@example.com",
            "username": "shortpass",
            "password": "abc",
            "confirm_password": "abc",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Password must be at least 6 characters" in response.text


@pytest.mark.asyncio
async def test_register_password_mismatch(client: AsyncClient):
    response = await client.post(
        "/register",
        data={
            "display_name": "Mismatch User",
            "email": "mismatch@example.com",
            "username": "mismatchuser",
            "password": "password123",
            "confirm_password": "differentpassword",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Passwords do not match" in response.text


@pytest.mark.asyncio
async def test_register_short_username(client: AsyncClient):
    response = await client.post(
        "/register",
        data={
            "display_name": "Short User",
            "email": "shortuser@example.com",
            "username": "ab",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Username must be at least 3 characters" in response.text


@pytest.mark.asyncio
async def test_register_empty_display_name(client: AsyncClient):
    response = await client.post(
        "/register",
        data={
            "display_name": "   ",
            "email": "emptyname@example.com",
            "username": "emptyname",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Display name is required" in response.text


@pytest.mark.asyncio
async def test_login_page_loads(client: AsyncClient):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "Welcome Back" in response.text


@pytest.mark.asyncio
async def test_login_success_customer(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/login",
        data={
            "username": customer_user.username,
            "password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/books"

    cookies = response.cookies
    assert "access_token" in cookies


@pytest.mark.asyncio
async def test_login_success_admin_redirects_to_admin(client: AsyncClient, admin_user: User):
    response = await client.post(
        "/login",
        data={
            "username": admin_user.username,
            "password": "adminpass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin"

    cookies = response.cookies
    assert "access_token" in cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/login",
        data={
            "username": customer_user.username,
            "password": "wrongpassword",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Invalid username or password" in response.text


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/login",
        data={
            "username": "nonexistentuser",
            "password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Invalid username or password" in response.text


@pytest.mark.asyncio
async def test_login_empty_fields(client: AsyncClient):
    response = await client.post(
        "/login",
        data={
            "username": "",
            "password": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Username and password are required" in response.text


@pytest.mark.asyncio
async def test_login_sets_httponly_cookie(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/login",
        data={
            "username": customer_user.username,
            "password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_header
    assert "httponly" in set_cookie_header.lower()


@pytest.mark.asyncio
async def test_logout_get(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_header


@pytest.mark.asyncio
async def test_logout_post(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_register_page_redirects_when_authenticated(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/books"


@pytest.mark.asyncio
async def test_login_page_redirects_when_authenticated(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/books"


@pytest.mark.asyncio
async def test_register_post_redirects_when_authenticated(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/register",
        data={
            "display_name": "Should Not Register",
            "email": "shouldnot@example.com",
            "username": "shouldnot",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/books"


@pytest.mark.asyncio
async def test_login_post_redirects_when_authenticated(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/login",
        data={
            "username": "someuser",
            "password": "somepass",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/books"


@pytest.mark.asyncio
async def test_jwt_cookie_grants_access_to_protected_route(client: AsyncClient, customer_user: User):
    token = create_access_token(
        data={
            "sub": str(customer_user.id),
            "username": customer_user.username,
            "role": customer_user.role,
        }
    )
    client.cookies.set("access_token", token)

    response = await client.get("/profile", follow_redirects=False)
    assert response.status_code == 200
    assert customer_user.display_name in response.text


@pytest.mark.asyncio
async def test_invalid_jwt_cookie_does_not_grant_access(client: AsyncClient):
    client.cookies.set("access_token", "invalid-token-value")

    response = await client.get("/cart", follow_redirects=False)
    assert response.status_code in (401, 403, 302)


@pytest.mark.asyncio
async def test_no_cookie_cannot_access_protected_route(client: AsyncClient):
    response = await client.get("/cart", follow_redirects=False)
    assert response.status_code in (401, 403, 302)


@pytest.mark.asyncio
async def test_register_invalid_username_characters(client: AsyncClient):
    response = await client.post(
        "/register",
        data={
            "display_name": "Bad Username",
            "email": "baduser@example.com",
            "username": "bad user!",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Username may only contain" in response.text