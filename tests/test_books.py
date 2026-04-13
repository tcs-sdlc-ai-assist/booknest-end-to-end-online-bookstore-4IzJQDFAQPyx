import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base
from models.user import User
from models.author import Author
from models.genre import Genre
from models.book import Book
from models.review import Review
from utils.security import hash_password, create_access_token


@pytest_asyncio.fixture
async def sample_author(db_session: AsyncSession) -> Author:
    author = Author(name="Test Author", bio="A test author bio.")
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def sample_genre(db_session: AsyncSession) -> Genre:
    genre = Genre(name="Test Genre")
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)
    return genre


@pytest_asyncio.fixture
async def second_genre(db_session: AsyncSession) -> Genre:
    genre = Genre(name="Second Genre")
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)
    return genre


@pytest_asyncio.fixture
async def sample_book(
    db_session: AsyncSession,
    sample_author: Author,
    sample_genre: Genre,
) -> Book:
    book = Book(
        title="Test Book One",
        isbn="978-0-0000-0001-0",
        price=19.99,
        stock=10,
        description="A test book description.",
        publication_year=2023,
        pages=300,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def second_book(
    db_session: AsyncSession,
    sample_author: Author,
    sample_genre: Genre,
) -> Book:
    book = Book(
        title="Second Book",
        isbn="978-0-0000-0002-0",
        price=9.99,
        stock=5,
        description="Another test book.",
        publication_year=2020,
        pages=150,
        author_id=sample_author.id,
        genre_id=sample_genre.id,
    )
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def book_in_second_genre(
    db_session: AsyncSession,
    sample_author: Author,
    second_genre: Genre,
) -> Book:
    book = Book(
        title="Genre Two Book",
        isbn="978-0-0000-0003-0",
        price=29.99,
        stock=3,
        description="A book in the second genre.",
        publication_year=2021,
        pages=400,
        author_id=sample_author.id,
        genre_id=second_genre.id,
    )
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_review(
    db_session: AsyncSession,
    customer_user: User,
    sample_book: Book,
) -> Review:
    review = Review(
        user_id=customer_user.id,
        book_id=sample_book.id,
        rating=4,
        text="Great book, really enjoyed it!",
    )
    db_session.add(review)
    await db_session.flush()
    await db_session.refresh(review)
    return review


@pytest_asyncio.fixture
async def second_customer(db_session: AsyncSession) -> User:
    user = User(
        display_name="Second Customer",
        email="secondcustomer@example.com",
        username="secondcustomer",
        password_hash=hash_password("password123"),
        role="customer",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_customer_client(
    client: AsyncClient,
    second_customer: User,
) -> AsyncClient:
    token_data = {
        "sub": str(second_customer.id),
        "username": second_customer.username,
        "role": second_customer.role,
    }
    token = create_access_token(data=token_data)
    client.cookies.set("access_token", token)
    return client


# ============================================================
# Catalog Listing Tests
# ============================================================


class TestCatalogListing:
    @pytest.mark.asyncio
    async def test_catalog_page_returns_200(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text

    @pytest.mark.asyncio
    async def test_catalog_page_empty_when_no_books(
        self,
        client: AsyncClient,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "No books found" in response.text

    @pytest.mark.asyncio
    async def test_catalog_shows_multiple_books(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text
        assert "Second Book" in response.text

    @pytest.mark.asyncio
    async def test_catalog_shows_book_price(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "19.99" in response.text

    @pytest.mark.asyncio
    async def test_catalog_shows_author_name(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Author" in response.text

    @pytest.mark.asyncio
    async def test_catalog_shows_genre_name(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Genre" in response.text


# ============================================================
# Search Tests
# ============================================================


class TestCatalogSearch:
    @pytest.mark.asyncio
    async def test_search_by_title(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?search=Test+Book", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text
        assert "Second Book" not in response.text

    @pytest.mark.asyncio
    async def test_search_by_author(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?search=Test+Author", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text

    @pytest.mark.asyncio
    async def test_search_no_results(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?search=NonExistentBook", follow_redirects=False)
        assert response.status_code == 200
        assert "No books found" in response.text

    @pytest.mark.asyncio
    async def test_search_case_insensitive(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?search=test+book", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text


# ============================================================
# Filter Tests
# ============================================================


class TestCatalogFilter:
    @pytest.mark.asyncio
    async def test_filter_by_genre(
        self,
        client: AsyncClient,
        sample_book: Book,
        book_in_second_genre: Book,
        second_genre: Genre,
    ):
        response = await client.get(
            f"/books?genre={second_genre.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Genre Two Book" in response.text
        assert "Test Book One" not in response.text

    @pytest.mark.asyncio
    async def test_filter_by_price_min(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?price_min=15.00", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text
        assert "Second Book" not in response.text

    @pytest.mark.asyncio
    async def test_filter_by_price_max(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?price_max=15.00", follow_redirects=False)
        assert response.status_code == 200
        assert "Second Book" in response.text
        assert "Test Book One" not in response.text

    @pytest.mark.asyncio
    async def test_filter_by_price_range(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
        book_in_second_genre: Book,
    ):
        response = await client.get(
            "/books?price_min=15.00&price_max=25.00", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Test Book One" in response.text
        assert "Second Book" not in response.text
        assert "Genre Two Book" not in response.text


# ============================================================
# Sort Tests
# ============================================================


class TestCatalogSort:
    @pytest.mark.asyncio
    async def test_sort_by_price_asc(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?sort=price_asc", follow_redirects=False)
        assert response.status_code == 200
        text = response.text
        pos_second = text.find("Second Book")
        pos_first = text.find("Test Book One")
        assert pos_second < pos_first

    @pytest.mark.asyncio
    async def test_sort_by_price_desc(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?sort=price_desc", follow_redirects=False)
        assert response.status_code == 200
        text = response.text
        pos_first = text.find("Test Book One")
        pos_second = text.find("Second Book")
        assert pos_first < pos_second

    @pytest.mark.asyncio
    async def test_sort_by_newest(
        self,
        client: AsyncClient,
        sample_book: Book,
        second_book: Book,
    ):
        response = await client.get("/books?sort=newest", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text
        assert "Second Book" in response.text


# ============================================================
# Pagination Tests
# ============================================================


class TestCatalogPagination:
    @pytest.mark.asyncio
    async def test_pagination_page_1(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?page=1", follow_redirects=False)
        assert response.status_code == 200
        assert "Test Book One" in response.text

    @pytest.mark.asyncio
    async def test_pagination_invalid_page_defaults(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?page=0", follow_redirects=False)
        assert response.status_code == 422 or response.status_code == 200

    @pytest.mark.asyncio
    async def test_pagination_beyond_last_page(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get("/books?page=999", follow_redirects=False)
        assert response.status_code == 200


# ============================================================
# Book Detail Tests
# ============================================================


class TestBookDetail:
    @pytest.mark.asyncio
    async def test_book_detail_returns_200(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Test Book One" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_description(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "A test book description." in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_author(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Test Author" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_price(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "19.99" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_isbn(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "978-0-0000-0001-0" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_stock(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "In Stock" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_not_found(
        self,
        client: AsyncClient,
    ):
        response = await client.get("/books/99999", follow_redirects=False)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_book_detail_shows_reviews(
        self,
        client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Great book, really enjoyed it!" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_no_reviews_message(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "No reviews yet" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_add_to_cart_for_authenticated_user(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Add to Cart" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_login_prompt_for_anonymous(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Sign in" in response.text


# ============================================================
# Review Creation Tests
# ============================================================


class TestReviewCreation:
    @pytest.mark.asyncio
    async def test_create_review_success(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 5, "text": "Excellent read!"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/books/{sample_book.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_create_review_appears_on_detail_page(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 4, "text": "Very good book."},
            follow_redirects=False,
        )
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Very good book." in response.text

    @pytest.mark.asyncio
    async def test_create_review_without_text(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 3, "text": ""},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_create_review_duplicate_rejected(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 3, "text": "Another review attempt."},
            follow_redirects=False,
        )
        assert response.status_code == 400
        assert "already reviewed" in response.text

    @pytest.mark.asyncio
    async def test_create_review_invalid_rating_too_low(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 0, "text": "Bad rating."},
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_review_invalid_rating_too_high(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 6, "text": "Too high."},
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_review_unauthenticated_redirects_to_login(
        self,
        client: AsyncClient,
        sample_book: Book,
    ):
        response = await client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 5, "text": "Should not work."},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_create_review_for_nonexistent_book(
        self,
        authenticated_client: AsyncClient,
    ):
        response = await authenticated_client.post(
            "/books/99999/reviews",
            data={"rating": 5, "text": "No book."},
            follow_redirects=False,
        )
        assert response.status_code in (303, 400)

    @pytest.mark.asyncio
    async def test_two_users_can_review_same_book(
        self,
        authenticated_client: AsyncClient,
        second_customer_client: AsyncClient,
        sample_book: Book,
    ):
        response1 = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 5, "text": "First user review."},
            follow_redirects=False,
        )
        assert response1.status_code == 303

        response2 = await second_customer_client.post(
            f"/books/{sample_book.id}/reviews",
            data={"rating": 3, "text": "Second user review."},
            follow_redirects=False,
        )
        assert response2.status_code == 303


# ============================================================
# Review Edit Tests
# ============================================================


class TestReviewEdit:
    @pytest.mark.asyncio
    async def test_edit_own_review_success(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/edit",
            data={"rating": 5, "text": "Updated review text."},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/books/{sample_book.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_edit_review_updates_content(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/edit",
            data={"rating": 2, "text": "Changed my mind."},
            follow_redirects=False,
        )
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Changed my mind." in response.text

    @pytest.mark.asyncio
    async def test_edit_other_users_review_rejected(
        self,
        second_customer_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await second_customer_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/edit",
            data={"rating": 1, "text": "Trying to edit someone else's review."},
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_edit_review_invalid_rating(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/edit",
            data={"rating": 0, "text": "Invalid rating."},
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_edit_review_unauthenticated_redirects(
        self,
        client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/edit",
            data={"rating": 3, "text": "Should not work."},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")


# ============================================================
# Review Delete Tests
# ============================================================


class TestReviewDelete:
    @pytest.mark.asyncio
    async def test_delete_own_review_success(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/books/{sample_book.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_delete_review_removes_from_page(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Great book, really enjoyed it!" not in response.text

    @pytest.mark.asyncio
    async def test_delete_other_users_review_rejected(
        self,
        second_customer_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await second_customer_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_review_unauthenticated_redirects(
        self,
        client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_review(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.post(
            f"/books/{sample_book.id}/reviews/99999/delete",
            follow_redirects=False,
        )
        assert response.status_code == 400


# ============================================================
# Admin Review Deletion Tests
# ============================================================


class TestAdminReviewDeletion:
    @pytest.mark.asyncio
    async def test_admin_can_delete_any_review(
        self,
        admin_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await admin_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/books/{sample_book.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_admin_delete_removes_review_from_page(
        self,
        admin_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        await admin_client.post(
            f"/books/{sample_book.id}/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        response = await admin_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Great book, really enjoyed it!" not in response.text


# ============================================================
# Book Detail with Reviews and Ratings
# ============================================================


class TestBookDetailWithReviews:
    @pytest.mark.asyncio
    async def test_book_detail_shows_average_rating(
        self,
        authenticated_client: AsyncClient,
        second_customer_client: AsyncClient,
        sample_book: Book,
        db_session: AsyncSession,
        customer_user: User,
        second_customer: User,
    ):
        review1 = Review(
            user_id=customer_user.id,
            book_id=sample_book.id,
            rating=4,
            text="Good.",
        )
        review2 = Review(
            user_id=second_customer.id,
            book_id=sample_book.id,
            rating=2,
            text="Not great.",
        )
        db_session.add(review1)
        db_session.add(review2)
        await db_session.flush()

        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "3.0" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_review_count(
        self,
        client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "1 review" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_shows_write_review_form_for_authenticated(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
    ):
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "Write a Review" in response.text

    @pytest.mark.asyncio
    async def test_book_detail_hides_review_form_if_already_reviewed(
        self,
        authenticated_client: AsyncClient,
        sample_book: Book,
        sample_review: Review,
    ):
        response = await authenticated_client.get(
            f"/books/{sample_book.id}", follow_redirects=False
        )
        assert response.status_code == 200
        assert "already reviewed" in response.text
        assert "Write a Review" not in response.text