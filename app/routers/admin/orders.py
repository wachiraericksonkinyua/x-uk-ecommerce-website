from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database import supabase
from app.dependencies import require_admin
from app.services.inventory import (
    STOCK_DEDUCTED_STATUSES,
    release_stock_once,
    restore_order_stock,
)
from app.utils.pagination import page_range
from app.utils.search import sanitize_search_term

router = APIRouter(prefix="/orders", tags=["Admin · Orders"])

VALID_STATUSES = {
    "Pending PIN",
    "Paid",
    "Processing",
    "Shipped",
    "Delivered",
    "Cancelled",
    "Payment Failed",
    "Refunded",
}


class AdminStatusUpdate(BaseModel):
    status: str


class OrderVerification(BaseModel):
    verified: bool = True
    note: Optional[str] = None


class RefundRequest(BaseModel):
    reason: Optional[str] = None
    amount: Optional[float] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refund_order(
    order: Dict[str, Any],
    admin_user: Any,
    *,
    reason: Optional[str] = None,
    amount: Optional[float] = None,
) -> bool:
    """Atomically mark an order Refunded and restore deducted stock once."""
    if order.get("status") == "Refunded":
        return False

    previous_status = order.get("status")
    order_id = order.get("id")
    if not order_id:
        raise HTTPException(status_code=400, detail="Order id is missing")

    refund_amount = amount
    if refund_amount is None:
        try:
            refund_amount = float(order.get("total_amount") or 0)
        except (TypeError, ValueError):
            refund_amount = 0.0

    update = {
        "status": "Refunded",
        "refunded_at": _now(),
        "refunded_by": getattr(admin_user, "id", None),
        "refund_reason": reason,
        "refund_amount": refund_amount,
    }
    res = (
        supabase.table("orders")
        .update(update)
        .eq("id", order_id)
        .neq("status", "Refunded")
        .execute()
    )
    if not res.data:
        return False

    # Cancelled/Payment Failed already had their stock restored. Paid,
    # Processing, Shipped, Delivered and pending orders still owe stock back.
    if previous_status in STOCK_DEDUCTED_STATUSES:
        restore_order_stock(
            order,
            reason="refund",
            created_by=getattr(admin_user, "id", None),
        )
    return True


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
            term = sanitize_search_term(search)
            if term:
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
def update_order_status(
    order_id: str,
    payload: AdminStatusUpdate,
    admin_user=Depends(require_admin),
):
    """Update an order's status.

    Cancelling goes through the inventory service so held stock is released
    exactly once. Selecting Refunded routes through the refund workflow so
    stock is restored as part of the transition.
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
            if not release_stock_once(order, "Cancelled", created_by=getattr(admin_user, "id", None)):
                # Already terminal (or stock no longer held): just set the status
                supabase.table("orders").update({"status": "Cancelled"}).eq("id", order_id).execute()
        elif payload.status == "Refunded":
            _refund_order(order, admin_user)
        else:
            supabase.table("orders").update({"status": payload.status}).eq("id", order_id).execute()

        return {"success": True, "message": f"Order {order_id} set to {payload.status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/verify")
def verify_order(
    order_id: str,
    payload: OrderVerification,
    admin_user=Depends(require_admin),
):
    """Flag a suspicious order as manually verified (or clear the flag)."""
    try:
        update = {
            "is_verified": payload.verified,
            "verification_note": payload.note,
            "verified_at": _now() if payload.verified else None,
            "verified_by": getattr(admin_user, "id", None) if payload.verified else None,
        }
        response = supabase.table("orders").update(update).eq("id", order_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Order not found")
        return {
            "success": True,
            "message": "Order verified" if payload.verified else "Verification cleared",
            "data": response.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/refund")
def refund_order(
    order_id: str,
    payload: Optional[RefundRequest] = None,
    admin_user=Depends(require_admin),
):
    """Refund an order: mark it Refunded and restore stock atomically once."""
    try:
        order_res = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        order = order_res.data
        if not isinstance(order, dict):
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") == "Refunded":
            return {
                "success": True,
                "message": "Order was already refunded",
                "data": order,
            }

        changed = _refund_order(
            order,
            admin_user,
            reason=payload.reason if payload else None,
            amount=payload.amount if payload else None,
        )
        if not changed:
            raise HTTPException(status_code=409, detail="Order could not be refunded")

        refreshed = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        return {
            "success": True,
            "message": "Order refunded and stock restored",
            "data": refreshed.data,
        }
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
