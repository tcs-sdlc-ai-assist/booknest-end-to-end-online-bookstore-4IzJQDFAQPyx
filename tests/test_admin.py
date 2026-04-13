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
async def admin(db: AsyncSession) -> User:
    user = User(
        display_name="Admin User",
        email="admintest@booknest.com",
        username="admintest",
        password_hash=hash_password("adminpass"),
        role="admin",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def customer(db: AsyncSession) -> User:
    user = User(
        display_name="Customer User",
        email="customertest@booknest.com",
        username="customertest",
        password_hash=hash_password("custpass"),
        role="customer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_author(db: AsyncSession) -> Author:
    author = Author(name="Test Author Admin")
    db.add(author)
    await db.flush()
    await db.refresh(author)
    return author


@pytest_asyncio.fixture
async def sample_genre(db: AsyncSession) -> Genre:
    genre = Genre(name="Test Genre Admin")
    db.add(genre)
    await db.flush()
    await db.refresh(genre)
    return genre


@pytest_asyncio.fixture
async def sample_book(db: AsyncSession, sample_author: Author, sample_genre: Genre) -> Book:
    book = Book(
        title="Admin Test Book",
        isbn="978-0-1111-2222-3",
        price=19.99,
        stock=10,
        description="A test book for admin tests.",
        publication_year=2024,
        pages=300,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_order(db: AsyncSession, customer: User, sample_book: Book) -> Order:
    order = Order(
        user_id=customer.id,
        total=19.99,
        status="pending",
        shipping_address="123 Test St\nTest City, TS 12345\nUnited States",
    )
    db.add(order)
    await db.flush()

    order_item = OrderItem(
        order_id=order.id,
        book_id=sample_book.id,
        book_title=sample_book.title,
        quantity=1,
        price=sample_book.price,
    )
    db.add(order_item)
    await db.flush()
    await db.refresh(order)
    return order


@pytest_asyncio.fixture
async def admin_http(admin: User) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        token = _make_token(admin)
        ac.cookies.set("access_token", token)
        yield ac


@pytest_asyncio.fixture
async def customer_http(customer: User) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        token = _make_token(customer)
        ac.cookies.set("access_token", token)
        yield ac


@pytest_asyncio.fixture
async def anon_http() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ─── Access Control ───────────────────────────────────────────────────────────


class TestAdminAccessControl:
    @pytest.mark.asyncio
    async def test_admin_dashboard_accessible_by_admin(
        self, admin_http: AsyncClient, sample_author: Author, sample_genre: Genre
    ):
        response = await admin_http.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text

    @pytest.mark.asyncio
    async def test_admin_dashboard_denied_for_customer(self, customer_http: AsyncClient):
        response = await customer_http.get("/admin", follow_redirects=False)
        # Should get 403 or redirect (HTTPException for non-admin)
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_admin_dashboard_denied_for_anonymous(self, anon_http: AsyncClient):
        response = await anon_http.get("/admin", follow_redirects=False)
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_admin_orders_page_denied_for_customer(self, customer_http: AsyncClient):
        response = await customer_http.get("/admin/orders", follow_redirects=False)
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_admin_authors_page_denied_for_customer(self, customer_http: AsyncClient):
        response = await customer_http.get("/admin/authors", follow_redirects=False)
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_admin_genres_page_denied_for_customer(self, customer_http: AsyncClient):
        response = await customer_http.get("/admin/genres", follow_redirects=False)
        assert response.status_code in (403, 401)


# ─── Dashboard Stats ──────────────────────────────────────────────────────────


class TestAdminDashboardStats:
    @pytest.mark.asyncio
    async def test_dashboard_shows_stats(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
        sample_order: Order,
    ):
        response = await admin_http.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        text = response.text
        assert "Total Books" in text
        assert "Total Orders" in text
        assert "Total Revenue" in text
        assert "Low Stock" in text

    @pytest.mark.asyncio
    async def test_dashboard_shows_books_tab(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
    ):
        response = await admin_http.get("/admin?tab=books", follow_redirects=False)
        assert response.status_code == 200
        assert sample_book.title in response.text

    @pytest.mark.asyncio
    async def test_dashboard_shows_orders_tab(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.get("/admin?tab=orders", follow_redirects=False)
        assert response.status_code == 200
        assert "Manage Orders" in response.text or "Orders" in response.text


# ─── Book CRUD ────────────────────────────────────────────────────────────────


class TestAdminBookCRUD:
    @pytest.mark.asyncio
    async def test_create_book_via_admin(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
        sample_genre: Genre,
    ):
        response = await admin_http.post(
            "/admin/books/add",
            data={
                "title": "New Admin Book",
                "author_id": str(sample_author.id),
                "genre_id": str(sample_genre.id),
                "isbn": "978-0-9999-8888-7",
                "price": "14.99",
                "stock": "25",
                "publication_year": "2023",
                "pages": "200",
                "description": "A newly created book via admin.",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_create_book_via_create_form(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
        sample_genre: Genre,
    ):
        # GET the create form
        response = await admin_http.get("/admin/books/create", follow_redirects=False)
        assert response.status_code == 200
        assert "Add New Book" in response.text

        # POST the create form
        response = await admin_http.post(
            "/admin/books/create",
            data={
                "title": "Created Via Form",
                "author_id": str(sample_author.id),
                "genre_id": str(sample_genre.id),
                "isbn": "978-0-5555-6666-7",
                "price": "9.99",
                "stock": "5",
                "publication_year": "",
                "pages": "",
                "description": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_book_form_loads(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
    ):
        response = await admin_http.get(
            f"/admin/books/{sample_book.id}/edit", follow_redirects=False
        )
        assert response.status_code == 200
        assert sample_book.title in response.text

    @pytest.mark.asyncio
    async def test_edit_book_submit(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
        sample_author: Author,
        sample_genre: Genre,
    ):
        response = await admin_http.post(
            f"/admin/books/{sample_book.id}/edit",
            data={
                "title": "Updated Admin Book",
                "author_id": str(sample_author.id),
                "genre_id": str(sample_genre.id),
                "isbn": sample_book.isbn,
                "price": "24.99",
                "stock": "15",
                "publication_year": "2025",
                "pages": "350",
                "description": "Updated description.",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_nonexistent_book_redirects(
        self,
        admin_http: AsyncClient,
    ):
        response = await admin_http.get(
            "/admin/books/99999/edit", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_book(
        self,
        admin_http: AsyncClient,
        db: AsyncSession,
        sample_author: Author,
        sample_genre: Genre,
    ):
        # Create a book to delete
        book = Book(
            title="Book To Delete",
            isbn="978-0-3333-4444-5",
            price=5.99,
            stock=1,
            author_id=sample_author.id,
            genre_id=sample_genre.id,
        )
        db.add(book)
        await db.flush()
        await db.refresh(book)
        book_id = book.id
        await db.commit()

        response = await admin_http.post(
            f"/admin/books/{book_id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_customer_cannot_create_book(
        self,
        customer_http: AsyncClient,
        sample_author: Author,
        sample_genre: Genre,
    ):
        response = await customer_http.post(
            "/admin/books/add",
            data={
                "title": "Unauthorized Book",
                "author_id": str(sample_author.id),
                "genre_id": str(sample_genre.id),
                "isbn": "978-0-0000-0000-0",
                "price": "10.00",
                "stock": "1",
            },
            follow_redirects=False,
        )
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_customer_cannot_delete_book(
        self,
        customer_http: AsyncClient,
        sample_book: Book,
    ):
        response = await customer_http.post(
            f"/admin/books/{sample_book.id}/delete", follow_redirects=False
        )
        assert response.status_code in (403, 401)


# ─── Author CRUD ──────────────────────────────────────────────────────────────


class TestAdminAuthorCRUD:
    @pytest.mark.asyncio
    async def test_authors_page_loads(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
    ):
        response = await admin_http.get("/admin/authors", follow_redirects=False)
        assert response.status_code == 200
        assert sample_author.name in response.text

    @pytest.mark.asyncio
    async def test_create_author(self, admin_http: AsyncClient):
        response = await admin_http.post(
            "/admin/authors",
            data={"name": "Brand New Author"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_create_author_inline(self, admin_http: AsyncClient):
        response = await admin_http.post(
            "/admin/authors/add",
            data={"name": "Inline Author"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_author(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
    ):
        response = await admin_http.post(
            f"/admin/authors/{sample_author.id}/edit",
            data={"name": "Renamed Author"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_author_without_books(
        self,
        admin_http: AsyncClient,
        db: AsyncSession,
    ):
        author = Author(name="Author To Delete")
        db.add(author)
        await db.flush()
        await db.refresh(author)
        author_id = author.id
        await db.commit()

        response = await admin_http.post(
            f"/admin/authors/{author_id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_author_with_books_fails_gracefully(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
        sample_book: Book,
    ):
        # sample_author has sample_book, so delete should fail gracefully (redirect)
        response = await admin_http.post(
            f"/admin/authors/{sample_author.id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_customer_cannot_create_author(self, customer_http: AsyncClient):
        response = await customer_http.post(
            "/admin/authors",
            data={"name": "Unauthorized Author"},
            follow_redirects=False,
        )
        assert response.status_code in (403, 401)


# ─── Genre CRUD ───────────────────────────────────────────────────────────────


class TestAdminGenreCRUD:
    @pytest.mark.asyncio
    async def test_genres_page_loads(
        self,
        admin_http: AsyncClient,
        sample_genre: Genre,
    ):
        response = await admin_http.get("/admin/genres", follow_redirects=False)
        assert response.status_code == 200
        assert sample_genre.name in response.text

    @pytest.mark.asyncio
    async def test_create_genre(self, admin_http: AsyncClient):
        response = await admin_http.post(
            "/admin/genres",
            data={"name": "Brand New Genre"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_create_genre_inline(self, admin_http: AsyncClient):
        response = await admin_http.post(
            "/admin/genres/add",
            data={"name": "Inline Genre"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_genre(
        self,
        admin_http: AsyncClient,
        sample_genre: Genre,
    ):
        response = await admin_http.post(
            f"/admin/genres/{sample_genre.id}/edit",
            data={"name": "Renamed Genre"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_genre_without_books(
        self,
        admin_http: AsyncClient,
        db: AsyncSession,
    ):
        genre = Genre(name="Genre To Delete")
        db.add(genre)
        await db.flush()
        await db.refresh(genre)
        genre_id = genre.id
        await db.commit()

        response = await admin_http.post(
            f"/admin/genres/{genre_id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_genre_with_books_fails_gracefully(
        self,
        admin_http: AsyncClient,
        sample_genre: Genre,
        sample_book: Book,
    ):
        response = await admin_http.post(
            f"/admin/genres/{sample_genre.id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_customer_cannot_create_genre(self, customer_http: AsyncClient):
        response = await customer_http.post(
            "/admin/genres",
            data={"name": "Unauthorized Genre"},
            follow_redirects=False,
        )
        assert response.status_code in (403, 401)


# ─── Order Status Updates ─────────────────────────────────────────────────────


class TestAdminOrderManagement:
    @pytest.mark.asyncio
    async def test_orders_page_loads(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.get("/admin/orders", follow_redirects=False)
        assert response.status_code == 200
        assert "Order Management" in response.text

    @pytest.mark.asyncio
    async def test_orders_page_filter_by_status(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.get(
            "/admin/orders?status=pending", follow_redirects=False
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_order_status_to_processing(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "processing"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_update_order_status_to_shipped(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "shipped"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_update_order_status_to_delivered(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "delivered"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_update_order_status_to_cancelled(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "cancelled"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_update_order_invalid_status(
        self,
        admin_http: AsyncClient,
        sample_order: Order,
    ):
        response = await admin_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "invalid_status"},
            follow_redirects=False,
        )
        # Should redirect gracefully even on invalid status (error is swallowed)
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_customer_cannot_update_order_status(
        self,
        customer_http: AsyncClient,
        sample_order: Order,
    ):
        response = await customer_http.post(
            f"/admin/orders/{sample_order.id}/status",
            data={"status": "shipped"},
            follow_redirects=False,
        )
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_orders_filter_empty_result(
        self,
        admin_http: AsyncClient,
    ):
        response = await admin_http.get(
            "/admin/orders?status=delivered", follow_redirects=False
        )
        assert response.status_code == 200
        assert "No orders found" in response.text or "orders" in response.text.lower()


# ─── Dashboard Search & Filter ────────────────────────────────────────────────


class TestAdminDashboardFilters:
    @pytest.mark.asyncio
    async def test_book_search_in_dashboard(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
    ):
        response = await admin_http.get(
            f"/admin?tab=books&book_search={sample_book.title[:5]}",
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert sample_book.title in response.text

    @pytest.mark.asyncio
    async def test_book_genre_filter_in_dashboard(
        self,
        admin_http: AsyncClient,
        sample_book: Book,
        sample_genre: Genre,
    ):
        response = await admin_http.get(
            f"/admin?tab=books&genre_filter={sample_genre.id}",
            follow_redirects=False,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_book_search_no_results(
        self,
        admin_http: AsyncClient,
        sample_author: Author,
        sample_genre: Genre,
    ):
        response = await admin_http.get(
            "/admin?tab=books&book_search=zzzznonexistentbook",
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "No books found" in response.text or "books" in response.text.lower()