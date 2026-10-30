from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import supabase

router = APIRouter(prefix="/inventory", tags=["Admin · Inventory"])


class StockUpdate(BaseModel):
    stock_quantity: int = Field(..., ge=0)


@router.get("/low-stock")
def low_stock(
    threshold: int = Query(5, ge=0, description="Show products with stock below this"),
):
    try:
        response = (
            supabase.table("products")
            .select("id, name, brand, stock_quantity, price")
            .lt("stock_quantity", threshold)
            .order("stock_quantity")
            .execute()
        )
        return {"success": True, "threshold": threshold, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{product_id}")
def set_stock(product_id: str, payload: StockUpdate):
    """Set the absolute stock quantity for a product."""
    try:
        response = (
            supabase.table("products")
            .update({"stock_quantity": payload.stock_quantity})
            .eq("id", product_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
