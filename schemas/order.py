from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


class CheckoutRequest(BaseModel):
    shipping_address: str

    @field_validator("shipping_address")
    @classmethod
    def shipping_address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Shipping address is required.")
        return v.strip()


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: str
    quantity: int
    price: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total: float
    status: str
    shipping_address: str
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    page: int
    pages: int