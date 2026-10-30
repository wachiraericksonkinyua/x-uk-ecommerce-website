from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.database import supabase

router = APIRouter(prefix="/dashboard", tags=["Admin · Dashboard"])

LOW_STOCK_THRESHOLD = 5


def _money(value) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@router.get("/summary")
def get_dashboard_summary():
    """Headline numbers for the admin dashboard."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # Revenue only counts paid orders. Status casing is not guaranteed
        # (webhooks/integrations may store "paid" / "PAID"), so match
        # case-insensitively rather than relying on an exact "Paid".
        paid_res = (
            supabase.table("orders")
            .select("total_amount, created_at")
            .ilike("status", "paid")
            .execute()
        )
        paid_orders_data = paid_res.data or []

        total_revenue = 0.0
        daily_revenue = 0.0
        for order in paid_orders_data:
            if not isinstance(order, dict):
                continue
            amount = _money(order.get("total_amount"))
            total_revenue += amount
            created_at = order.get("created_at")
            if isinstance(created_at, str) and created_at.startswith(today):
                daily_revenue += amount
        paid_orders = len(paid_orders_data)

        # Counts still need every order.
        orders_res = supabase.table("orders").select("status").execute()
        orders = orders_res.data or []
        total_orders = len(orders)
        pending_orders = sum(
            1
            for order in orders
            if isinstance(order, dict)
            and str(order.get("status") or "").strip().lower() == "pending pin"
        )

        low_stock_res = (
            supabase.table("products")
            .select("id, name, stock_quantity")
            .lt("stock_quantity", LOW_STOCK_THRESHOLD)
            .execute()
        )
        low_stock_products = low_stock_res.data or []

        profiles_res = supabase.table("profiles").select("user_id").execute()
        total_customers = len(profiles_res.data or [])

        return {
            "total_revenue": round(total_revenue, 2),
            "daily_revenue": round(daily_revenue, 2),
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "total_customers": total_customers,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "low_stock_products": low_stock_products,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
