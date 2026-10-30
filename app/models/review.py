"""Pydantic models shared across the reviews API."""

from typing import Optional

from pydantic import BaseModel, Field


class Review(BaseModel):
    id: Optional[str] = None
    product_id: str
    user_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: str
    # Moderation flag: new reviews start unapproved and are hidden from the
    # public storefront until an admin approves them.
    is_approved: bool = False
    created_at: Optional[str] = None
