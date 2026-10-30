from typing import Any, Dict

from app.database import supabase

# Order statuses during which product stock is being held
STOCK_HELD_STATUSES = {"Pending PIN", "Processing"}


def restore_order_stock(order: Dict[str, Any]) -> None:
    """Increment product stock back for every line item on an order."""
    items = order.get("items")
    if not isinstance(items, list):
        return

    for item in items:
        if not isinstance(item, dict):
            continue

        product_id = item.get("id") or item.get("product_id")
        if not product_id:
            continue

        try:
            quantity = int(item.get("qty"))
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        res = (
            supabase.table("products")
            .select("stock_quantity")
            .eq("id", product_id)
            .execute()
        )
        if not res.data or not isinstance(res.data[0], dict):
            continue

        try:
            current_stock = int(res.data[0].get("stock_quantity") or 0)
        except (TypeError, ValueError):
            current_stock = 0

        supabase.table("products").update(
            {"stock_quantity": current_stock + quantity}
        ).eq("id", product_id).execute()


def hold_order_stock(order: Dict[str, Any]) -> None:
    """Decrement product stock for every line item.

    Mirror of :func:`restore_order_stock`, used when a previously released order
    (e.g. a failed payment the customer actually paid for) is revived to ``Paid``.
    Stock never drops below zero.
    """
    items = order.get("items")
    if not isinstance(items, list):
        return

    for item in items:
        if not isinstance(item, dict):
            continue

        product_id = item.get("id") or item.get("product_id")
        if not product_id:
            continue

        try:
            quantity = int(item.get("qty"))
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        res = (
            supabase.table("products")
            .select("stock_quantity")
            .eq("id", product_id)
            .execute()
        )
        if not res.data or not isinstance(res.data[0], dict):
            continue

        try:
            current_stock = int(res.data[0].get("stock_quantity") or 0)
        except (TypeError, ValueError):
            current_stock = 0

        supabase.table("products").update(
            {"stock_quantity": max(0, current_stock - quantity)}
        ).eq("id", product_id).execute()


def release_stock_once(order: Dict[str, Any], new_status: str = "Payment Failed") -> bool:
    """Atomically move a still-held order to a failed/cancelled state and restore stock.

    The status guard in the UPDATE makes this safe against duplicate callback
    deliveries: only the request that actually flips the status restores stock.
    Returns True when this call performed the release.
    """
    if not isinstance(order, dict):
        return False

    current_status = order.get("status")
    if current_status not in STOCK_HELD_STATUSES:
        return False

    order_id = order.get("id")
    if not order_id:
        return False

    res = (
        supabase.table("orders")
        .update({"status": new_status})
        .eq("id", order_id)
        .eq("status", current_status)
        .execute()
    )
    if not res.data:
        # Another concurrent handler already transitioned this order
        return False

    restore_order_stock(order)
    return True
