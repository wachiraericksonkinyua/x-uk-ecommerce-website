from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import supabase
from app.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


@router.post("/add")
async def add_to_cart(item: CartItem, current_user=Depends(get_current_user)):
    try:
        # If the item already exists, increment; otherwise insert a new row.
        res = supabase.table("cart_items").select("*").eq("user_id", current_user.id).eq("product_id", item.product_id).execute()

        if res.data:
            new_qty = res.data[0]["quantity"] + item.quantity
            supabase.table("cart_items").update({"quantity": new_qty}).eq("id", res.data[0]["id"]).execute()
        else:
            supabase.table("cart_items").insert({
                "user_id": current_user.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
            }).execute()
        return {"message": "Added to cart"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_cart(current_user=Depends(get_current_user)):
    res = supabase.table("cart_items").select("*, products(*)").eq("user_id", current_user.id).execute()
    return {"data": res.data}


@router.patch("/{item_id}")
async def update_cart_item(item_id: str, payload: CartItemUpdate, current_user=Depends(get_current_user)):
    """Set a cart line's quantity (ownership enforced by user_id)."""
    res = (
        supabase.table("cart_items")
        .select("id, product_id")
        .eq("id", item_id)
        .eq("user_id", current_user.id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Cart item not found")

    # Refuse to add more than what is in stock.
    product_id = res.data[0]["product_id"]
    prod = supabase.table("products").select("stock_quantity").eq("id", product_id).execute()
    if prod.data and isinstance(prod.data[0], dict):
        stock = prod.data[0].get("stock_quantity")
        try:
            if stock is not None and payload.quantity > int(stock):
                raise HTTPException(status_code=400, detail="Not enough stock")
        except (TypeError, ValueError):
            pass

    supabase.table("cart_items").update({"quantity": payload.quantity}).eq("id", item_id).eq("user_id", current_user.id).execute()
    return {"message": "Cart updated"}


@router.delete("/{item_id}")
async def remove_cart_item(item_id: str, current_user=Depends(get_current_user)):
    res = (
        supabase.table("cart_items")
        .delete()
        .eq("id", item_id)
        .eq("user_id", current_user.id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Removed from cart"}


@router.delete("/")
async def clear_cart(current_user=Depends(get_current_user)):
    supabase.table("cart_items").delete().eq("user_id", current_user.id).execute()
    return {"message": "Cart cleared"}
