from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime


class CartItemAdd(BaseModel):
    book_id: int
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v

    @field_validator("book_id")
    @classmethod
    def book_id_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Book ID must be a positive integer")
        return v


class CartItemUpdate(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: str
    book_price: float
    quantity: int
    subtotal: float


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[CartItemResponse] = []
    total: float = 0.0
    item_count: int = 0