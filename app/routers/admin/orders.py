from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import supabase
from app.services.inventory import release_stock_once
from app.utils.pagination import page_range

router = APIRouter(prefix="/orders", tags=["Admin · Orders"])

VALID_STATUSES = {
    "Pending PIN",
    "Paid",
    "Processing",
    "Shipped",
    "Delivered",
    "Cancelled",
    "Payment Failed",
}


class AdminStatusUpdate(BaseModel):
    status: str


@router.get("")
def list_orders(
    status: Optional[str] = Query(None, description="Filter by order status"),
    search: Optional[str] = Query(None, description="Search reference, phone or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Paginated, filterable order list for the admin table."""
    try:
        query = supabase.table("orders").select("*", count="exact")
        if status:
            query = query.eq("status", status)
        if search:
            term = search.replace(",", "").strip()
            query = query.or_(
                f"order_reference.ilike.%{term}%,"
                f"customer_phone.ilike.%{term}%,"
                f"customer_email.ilike.%{term}%"
            )
        start, end = page_range(page, page_size)
        query = query.order("created_at", desc=True).range(start, end)
        response = query.execute()
        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total": response.count if response.count is not None else len(response.data or []),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}")
def get_order(order_id: str):
    try:
        response = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{order_id}/status")
def update_order_status(order_id: str, payload: AdminStatusUpdate):
    """Update an order's status.

    Cancelling goes through the inventory service so held stock is released
    exactly once.
    """
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed: {sorted(VALID_STATUSES)}",
        )
    try:
        order_res = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        order = order_res.data
        if not isinstance(order, dict):
            raise HTTPException(status_code=404, detail="Order not found")

        if payload.status == "Cancelled":
            if not release_stock_once(order, "Cancelled"):
                # Already terminal (or stock no longer held): just set the status
                supabase.table("orders").update({"status": "Cancelled"}).eq("id", order_id).execute()
        else:
            supabase.table("orders").update({"status": payload.status}).eq("id", order_id).execute()

        return {"success": True, "message": f"Order {order_id} set to {payload.status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/cancel")
def cancel_order(order_id: str):
    """Cancel an order and restore its held stock (idempotent)."""
    try:
        order_res = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        order = order_res.data
        if not isinstance(order, dict):
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") == "Cancelled":
            return {"success": True, "message": "Order was already cancelled"}

        if release_stock_once(order, "Cancelled"):
            return {"success": True, "message": "Order cancelled and stock restored"}

        # Not holding stock (e.g. already Paid/Delivered) — just mark cancelled
        supabase.table("orders").update({"status": "Cancelled"}).eq("id", order_id).execute()
        return {"success": True, "message": "Order marked as cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
