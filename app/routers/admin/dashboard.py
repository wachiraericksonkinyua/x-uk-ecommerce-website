from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.database import supabase

router = APIRouter(prefix="/dashboard", tags=["Admin · Dashboard"])

LOW_STOCK_THRESHOLD = 5
SERIES_DAYS = 14
RECENT_ORDER_LIMIT = 6
TOP_PRODUCT_LIMIT = 5

PAID_STATUSES = {"paid", "processing", "shipped", "delivered"}
PENDING_STATUSES = {"pending pin", "payment failed"}


def _money(value) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _status(value) -> str:
    return str(value or "").strip().lower()


def _row_date(value) -> str:
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, datetime):
        return value.date().isoformat()
    return ""


def _rows(data) -> List[Dict[str, Any]]:
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


@router.get("/summary")
def get_dashboard_summary():
    """Headline numbers, revenue trend, recent orders and stock health."""
    try:
        today = date.today()
        start = today - timedelta(days=SERIES_DAYS - 1)

        orders = _rows(supabase.table("orders").select("*").execute().data)
        products = _rows(
            supabase.table("products")
            .select("id, name, brand, stock_quantity, price")
            .execute()
            .data
        )
        profiles_res = supabase.table("profiles").select("user_id").execute()
        total_customers = len(profiles_res.data or [])

        series: Dict[str, Dict[str, Any]] = {
            (start + timedelta(days=offset)).isoformat(): {
                "date": (start + timedelta(days=offset)).isoformat(),
                "revenue": 0.0,
                "orders": 0,
            }
            for offset in range(SERIES_DAYS)
        }

        total_revenue = 0.0
        daily_revenue = 0.0
        refunded_revenue = 0.0
        paid_orders = 0
        pending_orders = 0
        status_counts: Dict[str, int] = defaultdict(int)
        product_units: Dict[str, Dict[str, Any]] = {}

        for order in orders:
            status = _status(order.get("status"))
            status_counts[status or "unknown"] += 1
            total = _money(order.get("total_amount"))
            created = _row_date(order.get("created_at"))

            if status == "refunded":
                refunded_revenue += _money(order.get("refund_amount")) or total
                continue

            if status in PENDING_STATUSES:
                pending_orders += 1
                continue

            if status not in PAID_STATUSES:
                continue

            paid_orders += 1
            total_revenue += total
            if created == today.isoformat():
                daily_revenue += total
            if created in series:
                series[created]["revenue"] += total
                series[created]["orders"] += 1

            items = order.get("items") if isinstance(order.get("items"), list) else []
            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    qty = int(item.get("qty") or 0)
                except (TypeError, ValueError):
                    qty = 0
                if qty <= 0:
                    continue
                product_id = str(item.get("id") or item.get("product_id") or "")
                if not product_id:
                    continue
                record = product_units.setdefault(
                    product_id,
                    {
                        "product_id": product_id,
                        "name": item.get("name") or "Unknown product",
                        "units": 0,
                        "revenue": 0.0,
                    },
                )
                record["units"] += qty
                record["revenue"] += _money(item.get("price")) * qty

        low_stock_products = []
        for product in products:
            try:
                stock = int(product.get("stock_quantity") or 0)
            except (TypeError, ValueError):
                stock = 0
            if stock < LOW_STOCK_THRESHOLD:
                low_stock_products.append(
                    {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "brand": product.get("brand"),
                        "stock_quantity": stock,
                        "price": product.get("price"),
                    }
                )
        low_stock_products.sort(key=lambda row: (row["stock_quantity"], row["name"] or ""))

        top_products = sorted(
            product_units.values(),
            key=lambda row: (row["units"], row["revenue"]),
            reverse=True,
        )[:TOP_PRODUCT_LIMIT]

        recent_orders = sorted(
            orders,
            key=lambda row: str(row.get("created_at") or ""),
            reverse=True,
        )[:RECENT_ORDER_LIMIT]
        recent_orders = [
            {
                "id": order.get("id"),
                "order_reference": order.get("order_reference"),
                "status": order.get("status"),
                "total_amount": order.get("total_amount"),
                "customer_email": order.get("customer_email"),
                "customer_phone": order.get("customer_phone"),
                "fulfillment": order.get("fulfillment"),
                "created_at": order.get("created_at"),
            }
            for order in recent_orders
        ]

        return {
            "total_revenue": round(total_revenue, 2),
            "daily_revenue": round(daily_revenue, 2),
            "refunded_revenue": round(refunded_revenue, 2),
            "net_revenue": round(total_revenue - refunded_revenue, 2),
            "total_orders": len(orders),
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "total_customers": total_customers,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "low_stock_products": low_stock_products,
            "revenue_series": list(series.values()),
            "status_breakdown": dict(sorted(status_counts.items())),
            "recent_orders": recent_orders,
            "top_products": top_products,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
