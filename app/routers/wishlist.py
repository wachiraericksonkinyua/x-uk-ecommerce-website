from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

class WishlistCreate(BaseModel):
    user_id: str
    product_id: str

@router.post("/")
def add_to_wishlist(item: WishlistCreate):
    try:
        response = supabase.table("wishlists").insert({
            "user_id": item.user_id,
            "product_id": item.product_id
        }).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
def get_user_wishlist(user_id: str):
    try:
        response = supabase.table("wishlists").select("id, created_at, products(*)").eq("user_id", user_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))