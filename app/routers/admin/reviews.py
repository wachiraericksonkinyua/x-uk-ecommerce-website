from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import supabase
from app.utils.pagination import page_range

router = APIRouter(prefix="/reviews", tags=["Admin · Reviews"])


class ReviewApproval(BaseModel):
    is_approved: bool


@router.get("")
def list_reviews(
    product_id: Optional[str] = Query(None, description="Filter by product"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        query = supabase.table("reviews").select("id, product_id, user_id, rating, comment, is_approved, created_at", count="exact")
        if product_id:
            query = query.eq("product_id", product_id)
        start, end = page_range(page, page_size)
        response = query.order("created_at", desc=True).range(start, end).execute()
        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total": response.count if response.count is not None else len(response.data or []),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{review_id}/approve")
def approve_review(review_id: str, payload: ReviewApproval):
    """Approve (show) or hide a review from the public storefront."""
    try:
        response = (
            supabase.table("reviews")
            .update({"is_approved": payload.is_approved})
            .eq("id", review_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Review not found")
        message = "Review approved" if payload.is_approved else "Review hidden"
        return {"success": True, "message": message, "data": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{review_id}")
def delete_review(review_id: str):
    try:
        response = supabase.table("reviews").delete().eq("id", review_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Review not found")
        return {"success": True, "message": "Review deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
