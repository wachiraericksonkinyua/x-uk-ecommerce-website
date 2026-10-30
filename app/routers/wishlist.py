from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import supabase
from app.dependencies import get_current_user

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


class WishlistCreate(BaseModel):
    product_id: str


@router.post("/")
def add_to_wishlist(item: WishlistCreate, current_user=Depends(get_current_user)):
    try:
        response = supabase.table("wishlists").insert({
            "user_id": current_user.id,
            "product_id": item.product_id,
        }).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_my_wishlist(current_user=Depends(get_current_user)):
    try:
        response = (
            supabase.table("wishlists")
            .select("id, created_at, products(*)")
            .eq("user_id", current_user.id)
            .execute()
        )
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}")
def remove_from_wishlist(product_id: str, current_user=Depends(get_current_user)):
    """Remove a product from my wishlist (by product id, for easy toggling)."""
    try:
        response = (
            supabase.table("wishlists")
            .delete()
            .eq("user_id", current_user.id)
            .eq("product_id", product_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Wishlist item not found")
        return {"success": True, "message": "Removed from wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
