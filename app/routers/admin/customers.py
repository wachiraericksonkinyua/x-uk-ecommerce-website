from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import supabase
from app.utils.pagination import page_range

router = APIRouter(prefix="/customers", tags=["Admin · Customers"])


class RoleUpdate(BaseModel):
    role: Literal["admin", "staff", "customer"]


@router.get("")
def list_customers(
    search: Optional[str] = Query(None, description="Search by name or phone"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        query = supabase.table("profiles").select("*", count="exact")
        if search:
            term = search.replace(",", "").strip()
            query = query.or_(f"full_name.ilike.%{term}%,phone_number.ilike.%{term}%")
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


@router.get("/{user_id}")
def get_customer(user_id: str):
    """A customer's profile plus their order history."""
    try:
        profile_res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        orders_res = (
            supabase.table("orders")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if not profile_res.data and not orders_res.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {
            "success": True,
            "profile": profile_res.data[0] if profile_res.data else None,
            "orders": orders_res.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}/role")
def update_customer_role(user_id: str, payload: RoleUpdate):
    """Grant or revoke a user's role. Keeps `is_admin` in sync with `role`."""
    try:
        data = {"role": payload.role, "is_admin": payload.role == "admin"}

        # Profiles are keyed by `user_id` in the reconciled schema, but older
        # tables use `id` — try both so the toggle works either way. Some
        # schemas also lack `is_admin`; fall back to updating just `role`.
        updated = None
        for column in ("user_id", "id"):
            try:
                res = supabase.table("profiles").update(data).eq(column, user_id).execute()
            except Exception:
                try:
                    res = (
                        supabase.table("profiles")
                        .update({"role": payload.role})
                        .eq(column, user_id)
                        .execute()
                    )
                except Exception:
                    continue
            if res.data:
                updated = res.data[0]
                break

        if updated is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "data": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
