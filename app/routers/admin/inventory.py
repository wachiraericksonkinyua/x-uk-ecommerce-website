from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import supabase
from app.dependencies import require_admin
from app.services.inventory import record_inventory_movement

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
def set_stock(
    product_id: str,
    payload: StockUpdate,
    admin_user=Depends(require_admin),
):
    """Set the absolute stock quantity for a product and log the movement."""
    try:
        current_res = (
            supabase.table("products")
            .select("id, name, stock_quantity")
            .eq("id", product_id)
            .execute()
        )
        if not current_res.data or not isinstance(current_res.data[0], dict):
            raise HTTPException(status_code=404, detail="Product not found")
        before = int(current_res.data[0].get("stock_quantity") or 0)

        response = (
            supabase.table("products")
            .update({"stock_quantity": payload.stock_quantity})
            .eq("id", product_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")

        record_inventory_movement(
            product_id=product_id,
            change_qty=payload.stock_quantity - before,
            quantity_before=before,
            quantity_after=payload.stock_quantity,
            reason="adjustment",
            note="Admin stock update",
            created_by=getattr(admin_user, "id", None),
        )
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
