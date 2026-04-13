from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(20), nullable=False, unique=True)
    price = Column(Float, nullable=False, default=0.0)
    stock = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    pages = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_books_title", "title"),
        Index("idx_books_author_id", "author_id"),
    )

    author = relationship("Author", back_populates="books", lazy="selectin")
    genre = relationship("Genre", back_populates="books", lazy="selectin")
    reviews = relationship("Review", back_populates="book", lazy="selectin", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="book", lazy="selectin", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="book", lazy="selectin")