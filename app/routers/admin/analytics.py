from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.database import supabase

router = APIRouter(prefix="/analytics", tags=["Admin · Analytics"])

PAID_STATUSES = {"paid", "processing", "shipped", "delivered"}
PENDING_STATUSES = {"pending pin", "payment failed"}
LOW_STOCK_DEFAULT = 5


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _row_date(value: Any) -> str:
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, datetime):
        return value.date().isoformat()
    return ""


def _safe_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


@router.get("/sales")
def sales_analytics(
    days: int = Query(14, ge=7, le=90, description="Daily series window"),
    low_stock_threshold: int = Query(LOW_STOCK_DEFAULT, ge=0, le=100),
):
    """Revenue, product movement, stock alerts and order verification data."""
    try:
        orders = _safe_rows(supabase.table("orders").select("*").execute().data)
        products = _safe_rows(
            supabase.table("products")
            .select("id, name, brand, stock_quantity, price, category_id")
            .execute()
            .data
        )
        try:
            movements = _safe_rows(
                supabase.table("inventory_movements")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
                .data
            )
        except Exception:
            movements = []

        today = date.today()
        start = today - timedelta(days=days - 1)
        daily: Dict[str, Dict[str, Any]] = {
            (start + timedelta(days=offset)).isoformat(): {
                "date": (start + timedelta(days=offset)).isoformat(),
                "revenue": 0.0,
                "refunded": 0.0,
                "orders": 0,
                "units": 0,
            }
            for offset in range(days)
        }

        gross_revenue = 0.0
        refunded_revenue = 0.0
        units_sold = 0
        paid_orders = 0
        pending_orders = 0
        refunded_orders = 0
        verified_orders = 0
        unverified_orders = 0
        status_counts: Dict[str, int] = defaultdict(int)
        payment_counts: Dict[str, int] = defaultdict(int)
        product_units: Dict[str, Dict[str, Any]] = {}

        for order in orders:
            status = _status(order.get("status"))
            status_counts[status or "unknown"] += 1
            payment_counts[str(order.get("payment_method") or "unknown")] += 1

            if order.get("is_verified"):
                verified_orders += 1
            elif status in {"paid", "processing", "shipped", "delivered"}:
                unverified_orders += 1

            total = _number(order.get("total_amount"))
            created = _row_date(order.get("created_at"))
            items = order.get("items") if isinstance(order.get("items"), list) else []

            if status == "refunded":
                refunded_orders += 1
                refunded_revenue += _number(order.get("refund_amount")) or total
                if created in daily:
                    daily[created]["refunded"] += _number(order.get("refund_amount")) or total
                continue

            if status in PENDING_STATUSES:
                pending_orders += 1
                continue

            if status not in PAID_STATUSES:
                continue

            paid_orders += 1
            gross_revenue += total
            if created in daily:
                daily[created]["revenue"] += total
                daily[created]["orders"] += 1

            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    qty = int(item.get("qty") or 0)
                except (TypeError, ValueError):
                    qty = 0
                if qty <= 0:
                    continue
                units_sold += qty
                if created in daily:
                    daily[created]["units"] += qty

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
                record["revenue"] += _number(item.get("price")) * qty

        product_names = {
            str(product.get("id")): product.get("name") for product in products
        }
        for movement in movements:
            movement["product_name"] = product_names.get(str(movement.get("product_id")))

        stock_alerts = []
        for product in products:
            try:
                stock = int(product.get("stock_quantity") or 0)
            except (TypeError, ValueError):
                stock = 0
            if stock > low_stock_threshold:
                continue
            product_id = str(product.get("id") or "")
            sold = product_units.get(product_id, {}).get("units", 0)
            stock_alerts.append(
                {
                    "id": product_id,
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "stock_quantity": stock,
                    "price": product.get("price"),
                    "units_sold": sold,
                }
            )
        stock_alerts.sort(key=lambda row: (row["stock_quantity"], row["name"] or ""))

        top_products = sorted(
            product_units.values(),
            key=lambda row: (row["units"], row["revenue"]),
            reverse=True,
        )[:10]

        return {
            "success": True,
            "window_days": days,
            "low_stock_threshold": low_stock_threshold,
            "revenue": {
                "gross": round(gross_revenue, 2),
                "refunded": round(refunded_revenue, 2),
                "net": round(gross_revenue - refunded_revenue, 2),
                "today": round(daily.get(today.isoformat(), {}).get("revenue", 0.0), 2),
            },
            "orders": {
                "total": len(orders),
                "paid": paid_orders,
                "pending": pending_orders,
                "refunded": refunded_orders,
                "verified": verified_orders,
                "unverified_paid": unverified_orders,
            },
            "units_sold": units_sold,
            "status_breakdown": dict(sorted(status_counts.items())),
            "payment_breakdown": dict(sorted(payment_counts.items())),
            "daily_series": list(daily.values()),
            "top_products": top_products,
            "stock_alerts": stock_alerts,
            "movements": movements,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
