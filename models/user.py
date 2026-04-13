from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    display_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="customer")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), default=datetime.utcnow)

    reviews = relationship("Review", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", lazy="selectin", cascade="all, delete-orphan")