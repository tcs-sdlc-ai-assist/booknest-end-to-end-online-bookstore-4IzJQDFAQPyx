from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ReviewCreate(BaseModel):
    rating: int
    text: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_must_be_between_1_and_5(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("text")
    @classmethod
    def text_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("Review text must be at most 1000 characters")
        return v


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    text: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_must_be_between_1_and_5(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("text")
    @classmethod
    def text_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("Review text must be at most 1000 characters")
        return v


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: str
    rating: int
    text: Optional[str] = None
    created_at: datetime