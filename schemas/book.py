from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AuthorCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Author name must not be empty")
        return v.strip()


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GenreCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Genre name must not be empty")
        return v.strip()


class GenreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class BookCreate(BaseModel):
    title: str
    author_id: int
    genre_id: int
    price: float
    description: Optional[str] = None
    isbn: str
    stock: int = 0
    publication_year: Optional[int] = None
    pages: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()

    @field_validator("isbn")
    @classmethod
    def isbn_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ISBN must not be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stock must be non-negative")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    genre_id: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    stock: Optional[int] = None
    publication_year: Optional[int] = None
    pages: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip() if v is not None else v

    @field_validator("isbn")
    @classmethod
    def isbn_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("ISBN must not be empty")
        return v.strip() if v is not None else v

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Stock must be non-negative")
        return v


class ReviewInBook(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: str
    rating: int
    text: Optional[str] = None
    created_at: datetime


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    genre: str
    price: float
    description: Optional[str] = None
    isbn: str
    stock: int
    publication_year: Optional[int] = None
    pages: Optional[int] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    created_at: datetime


class BookDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    genre: str
    price: float
    description: Optional[str] = None
    isbn: str
    stock: int
    publication_year: Optional[int] = None
    pages: Optional[int] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    reviews: list[ReviewInBook] = []
    created_at: datetime


class BookListResponse(BaseModel):
    books: list[BookResponse]
    total: int
    page: int
    pages: int