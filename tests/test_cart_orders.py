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
from models.author import Author
from models.book import Book
from models.cart_item import CartItem
from models.genre import Genre
from models.order import Order, OrderItem
from models.user import User
from utils.security import hash_password, create_access_token

from tests.conftest import TestSessionLocal, override_get_db, test_engine


def _make_token(user: User) -> str:
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    return create_access_token(data=token_data)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def sample_user(db: AsyncSession) -> User:
    user = User(
        display_name="Cart Tester",
        email="carttester@example.com",
        username="carttester",
        password_hash=hash_password("testpass123"),
        role="customer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db: AsyncSession) -> User:
    user = User(
        display_name="Other User",
        email="otheruser@example.com",
        username="otheruser",
        password_hash=hash_password("otherpass123"),
        role="customer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_author(db: AsyncSession) -> Author:
    author = Author(name="Cart Test Author", bio="Test bio")
    db.add(author)
    await db.flush()
    await db.refresh(author)
    return author


@pytest_asyncio.fixture
async def sample_genre(db: AsyncSession) -> Genre:
    genre = Genre(name="Cart Test Genre")
    db.add(genre)
    await db.flush()
    await db.refresh(genre)
    return genre


@pytest_asyncio.fixture
async def sample_book(db: AsyncSession, sample_author: Author, sample_genre: Genre) -> Book:
    book = Book(
        title="Cart Test Book",
        isbn="978-0-0000-0001-0",
        price=15.99,
        stock=10,
        description="A book for cart testing.",
        publication_year=2024,
        pages=200,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_book_low_stock(db: AsyncSession, sample_author: Author, sample_genre: Genre) -> Book:
    book = Book(
        title="Low Stock Book",
        isbn="978-0-0000-0002-0",
        price=9.99,
        stock=2,
        description="A book with low stock.",
        publication_year=2023,
        pages=150,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_book_out_of_stock(db: AsyncSession, sample_author: Author, sample_genre: Genre) -> Book:
    book = Book(
        title="Out of Stock Book",
        isbn="978-0-0000-0003-0",
        price=19.99,
        stock=0,
        description="A book that is out of stock.",
        publication_year=2022,
        pages=300,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


@pytest_asyncio.fixture
async def auth_client(sample_user: User) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        token = _make_token(sample_user)
        ac.cookies.set("access_token", token)
        yield ac


@pytest_asyncio.fixture
async def other_auth_client(other_user: User) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        token = _make_token(other_user)
        ac.cookies.set("access_token", token)
        yield ac


@pytest_asyncio.fixture
async def unauth_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


class TestCartAddItem:
    @pytest.mark.asyncio
    async def test_add_to_cart_success(self, auth_client: AsyncClient, sample_book: Book):
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_add_to_cart_multiple_quantity(self, auth_client: AsyncClient, sample_book: Book):
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 3},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_add_to_cart_out_of_stock_redirects_with_error(
        self, auth_client: AsyncClient, sample_book_out_of_stock: Book
    ):
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_out_of_stock.id, "quantity": 1},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()

    @pytest.mark.asyncio
    async def test_add_to_cart_exceeds_stock_redirects_with_error(
        self, auth_client: AsyncClient, sample_book_low_stock: Book
    ):
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 5},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()

    @pytest.mark.asyncio
    async def test_add_to_cart_unauthenticated_returns_401(
        self, unauth_client: AsyncClient, sample_book: Book
    ):
        response = await unauth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=False,
        )
        assert response.status_code in (401, 303)

    @pytest.mark.asyncio
    async def test_add_to_cart_increments_existing_item(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 2},
            follow_redirects=False,
        )
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 3},
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestCartUpdateItem:
    @pytest.mark.asyncio
    async def test_update_cart_item_quantity(self, auth_client: AsyncClient, sample_book: Book):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=False,
        )
        response = await auth_client.post(
            f"/cart/{sample_book.id}",
            data={"quantity": 5},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "success" in location.lower()

    @pytest.mark.asyncio
    async def test_update_cart_item_exceeds_stock(
        self, auth_client: AsyncClient, sample_book_low_stock: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 1},
            follow_redirects=False,
        )
        response = await auth_client.post(
            f"/cart/{sample_book_low_stock.id}",
            data={"quantity": 100},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()

    @pytest.mark.asyncio
    async def test_update_nonexistent_cart_item(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/cart/99999",
            data={"quantity": 1},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()


class TestCartRemoveItem:
    @pytest.mark.asyncio
    async def test_remove_cart_item_success(self, auth_client: AsyncClient, sample_book: Book):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=False,
        )
        response = await auth_client.post(
            f"/cart/{sample_book.id}/remove",
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "success" in location.lower()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_cart_item(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/cart/99999/remove",
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()


class TestCartPage:
    @pytest.mark.asyncio
    async def test_cart_page_loads_for_authenticated_user(self, auth_client: AsyncClient):
        response = await auth_client.get("/cart", follow_redirects=False)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cart_page_shows_empty_cart(self, auth_client: AsyncClient):
        response = await auth_client.get("/cart", follow_redirects=True)
        assert response.status_code == 200
        assert "cart" in response.text.lower()

    @pytest.mark.asyncio
    async def test_cart_page_shows_added_items(self, auth_client: AsyncClient, sample_book: Book):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 2},
            follow_redirects=True,
        )
        response = await auth_client.get("/cart", follow_redirects=True)
        assert response.status_code == 200
        assert sample_book.title in response.text


class TestCheckout:
    @pytest.mark.asyncio
    async def test_checkout_page_loads(self, auth_client: AsyncClient, sample_book: Book):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        response = await auth_client.get("/checkout", follow_redirects=False)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_checkout_page_redirects_with_empty_cart(self, auth_client: AsyncClient):
        response = await auth_client.get("/checkout", follow_redirects=False)
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "/cart" in location

    @pytest.mark.asyncio
    async def test_checkout_success_creates_order(
        self, auth_client: AsyncClient, sample_book: Book, db: AsyncSession
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 2},
            follow_redirects=True,
        )
        response = await auth_client.post(
            "/checkout",
            data={
                "street": "123 Test Street",
                "city": "Testville",
                "state": "TS",
                "zip": "12345",
                "country": "United States",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "/orders/" in location

    @pytest.mark.asyncio
    async def test_checkout_clears_cart(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        await auth_client.post(
            "/checkout",
            data={
                "street": "456 Clear St",
                "city": "Cleartown",
                "state": "CL",
                "zip": "67890",
                "country": "United States",
            },
            follow_redirects=True,
        )
        cart_response = await auth_client.get("/cart", follow_redirects=True)
        assert cart_response.status_code == 200
        assert "empty" in cart_response.text.lower() or "haven" in cart_response.text.lower()

    @pytest.mark.asyncio
    async def test_checkout_decrements_stock(
        self, auth_client: AsyncClient, sample_book: Book, db: AsyncSession
    ):
        original_stock = sample_book.stock
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 3},
            follow_redirects=True,
        )
        await auth_client.post(
            "/checkout",
            data={
                "street": "789 Stock St",
                "city": "Stockton",
                "state": "ST",
                "zip": "11111",
                "country": "United States",
            },
            follow_redirects=True,
        )
        await db.expire_all()
        result = await db.execute(select(Book).where(Book.id == sample_book.id))
        updated_book = result.scalar_one_or_none()
        assert updated_book is not None
        assert updated_book.stock == original_stock - 3

    @pytest.mark.asyncio
    async def test_checkout_missing_address_fields(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        response = await auth_client.post(
            "/checkout",
            data={
                "street": "",
                "city": "",
                "state": "",
                "zip": "",
                "country": "",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_checkout_with_out_of_stock_item_shows_warning(
        self,
        auth_client: AsyncClient,
        sample_book_low_stock: Book,
        db: AsyncSession,
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 1},
            follow_redirects=True,
        )
        result = await db.execute(select(Book).where(Book.id == sample_book_low_stock.id))
        book = result.scalar_one()
        book.stock = 0
        await db.flush()
        await db.commit()

        response = await auth_client.get("/checkout", follow_redirects=True)
        assert response.status_code == 200
        assert "out of stock" in response.text.lower() or "available" in response.text.lower()


class TestOrderHistory:
    @pytest.mark.asyncio
    async def test_orders_page_loads_for_authenticated_user(self, auth_client: AsyncClient):
        response = await auth_client.get("/orders", follow_redirects=False)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_orders_page_shows_no_orders(self, auth_client: AsyncClient):
        response = await auth_client.get("/orders", follow_redirects=True)
        assert response.status_code == 200
        assert "no orders" in response.text.lower() or "haven" in response.text.lower()

    @pytest.mark.asyncio
    async def test_orders_page_shows_placed_order(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        await auth_client.post(
            "/checkout",
            data={
                "street": "100 Order St",
                "city": "Orderville",
                "state": "OR",
                "zip": "22222",
                "country": "United States",
            },
            follow_redirects=True,
        )
        response = await auth_client.get("/orders", follow_redirects=True)
        assert response.status_code == 200
        assert "pending" in response.text.lower() or "order" in response.text.lower()

    @pytest.mark.asyncio
    async def test_orders_page_filter_by_status(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        await auth_client.post(
            "/checkout",
            data={
                "street": "200 Filter St",
                "city": "Filterville",
                "state": "FL",
                "zip": "33333",
                "country": "United States",
            },
            follow_redirects=True,
        )
        response = await auth_client.get("/orders?status=pending", follow_redirects=True)
        assert response.status_code == 200

        response_none = await auth_client.get("/orders?status=delivered", follow_redirects=True)
        assert response_none.status_code == 200


class TestOrderDetail:
    @pytest.mark.asyncio
    async def test_order_detail_page_loads(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 2},
            follow_redirects=True,
        )
        checkout_response = await auth_client.post(
            "/checkout",
            data={
                "street": "300 Detail St",
                "city": "Detailtown",
                "state": "DT",
                "zip": "44444",
                "country": "United States",
            },
            follow_redirects=False,
        )
        assert checkout_response.status_code == 303
        location = checkout_response.headers.get("location", "")
        assert "/orders/" in location

        response = await auth_client.get(location, follow_redirects=True)
        assert response.status_code == 200
        assert sample_book.title in response.text

    @pytest.mark.asyncio
    async def test_order_detail_shows_shipping_address(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        checkout_response = await auth_client.post(
            "/checkout",
            data={
                "street": "400 Address Ln",
                "city": "Addressville",
                "state": "AD",
                "zip": "55555",
                "country": "United States",
            },
            follow_redirects=False,
        )
        location = checkout_response.headers.get("location", "")
        response = await auth_client.get(location, follow_redirects=True)
        assert response.status_code == 200
        assert "400 Address Ln" in response.text
        assert "Addressville" in response.text

    @pytest.mark.asyncio
    async def test_order_detail_shows_total(
        self, auth_client: AsyncClient, sample_book: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 2},
            follow_redirects=True,
        )
        checkout_response = await auth_client.post(
            "/checkout",
            data={
                "street": "500 Total St",
                "city": "Totaltown",
                "state": "TT",
                "zip": "66666",
                "country": "United States",
            },
            follow_redirects=False,
        )
        location = checkout_response.headers.get("location", "")
        response = await auth_client.get(location, follow_redirects=True)
        assert response.status_code == 200
        expected_total = f"{sample_book.price * 2:.2f}"
        assert expected_total in response.text

    @pytest.mark.asyncio
    async def test_order_detail_nonexistent_order_returns_404(self, auth_client: AsyncClient):
        response = await auth_client.get("/orders/99999", follow_redirects=True)
        assert response.status_code == 404 or "not found" in response.text.lower()


class TestOrderOwnership:
    @pytest.mark.asyncio
    async def test_user_cannot_view_other_users_order(
        self,
        auth_client: AsyncClient,
        other_auth_client: AsyncClient,
        sample_book: Book,
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book.id, "quantity": 1},
            follow_redirects=True,
        )
        checkout_response = await auth_client.post(
            "/checkout",
            data={
                "street": "600 Private St",
                "city": "Privatetown",
                "state": "PV",
                "zip": "77777",
                "country": "United States",
            },
            follow_redirects=False,
        )
        location = checkout_response.headers.get("location", "")
        assert "/orders/" in location

        response = await other_auth_client.get(location, follow_redirects=True)
        assert response.status_code == 404 or "not found" in response.text.lower()

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_view_orders(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/orders", follow_redirects=False)
        assert response.status_code in (401, 303)

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_view_order_detail(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/orders/1", follow_redirects=False)
        assert response.status_code in (401, 303)


class TestStockEnforcement:
    @pytest.mark.asyncio
    async def test_cannot_add_more_than_stock_to_cart(
        self, auth_client: AsyncClient, sample_book_low_stock: Book
    ):
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 100},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()

    @pytest.mark.asyncio
    async def test_cannot_update_cart_beyond_stock(
        self, auth_client: AsyncClient, sample_book_low_stock: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 1},
            follow_redirects=True,
        )
        response = await auth_client.post(
            f"/cart/{sample_book_low_stock.id}",
            data={"quantity": 50},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()

    @pytest.mark.asyncio
    async def test_add_to_cart_then_add_more_exceeds_stock(
        self, auth_client: AsyncClient, sample_book_low_stock: Book
    ):
        await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 2},
            follow_redirects=True,
        )
        response = await auth_client.post(
            "/cart/add",
            data={"book_id": sample_book_low_stock.id, "quantity": 1},
            follow_redirects=False,
        )
        assert response.status_code == 303
        location = response.headers.get("location", "")
        assert "error" in location.lower()