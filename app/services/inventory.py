from typing import Any, Dict, Optional

from app.database import supabase

# Statuses where stock is held but payment has not been confirmed. A late
# failure callback must only release stock from these states.
STOCK_HELD_STATUSES = {"Pending PIN", "Processing"}

# Statuses where one physical unit has already been taken out of stock and a
# refund should put it back. Cancelled/Payment Failed are deliberately excluded
# because their stock was already restored.
STOCK_DEDUCTED_STATUSES = {"Pending PIN", "Processing", "Paid", "Shipped", "Delivered"}


def record_inventory_movement(
    *,
    product_id: Optional[str],
    change_qty: int,
    reason: str,
    order_id: Optional[str] = None,
    quantity_before: Optional[int] = None,
    quantity_after: Optional[int] = None,
    unit_price: Any = None,
    note: Optional[str] = None,
    created_by: Optional[str] = None,
) -> None:
    """Append an inventory ledger row.

    Logging must never break the business operation (e.g. if migration 007 has
    not been applied yet), so write failures are deliberately swallowed and
    surfaced only in the server log.
    """
    try:
        supabase.table("inventory_movements").insert(
            {
                "product_id": product_id,
                "order_id": order_id,
                "change_qty": int(change_qty),
                "quantity_before": quantity_before,
                "quantity_after": quantity_after,
                "unit_price": unit_price,
                "reason": reason,
                "note": note,
                "created_by": created_by,
            }
        ).execute()
    except Exception as exc:  # pragma: no cover - depends on live schema
        print(f"[inventory] movement log skipped: {exc}")


def restore_items(
    items: Any,
    *,
    order_id: Optional[str] = None,
    reason: str = "stock_restore",
    created_by: Optional[str] = None,
) -> None:
    """Increment product stock for an explicit list of line items.

    Used both by :func:`restore_order_stock` and by checkout rollback, which
    must restore *only* the lines that were actually decremented. Restoring the
    whole order would invent stock for lines that failed before being held.
    """
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

        new_stock = current_stock + quantity
        supabase.table("products").update(
            {"stock_quantity": new_stock}
        ).eq("id", product_id).execute()

        record_inventory_movement(
            product_id=product_id,
            order_id=order_id,
            change_qty=quantity,
            quantity_before=current_stock,
            quantity_after=new_stock,
            unit_price=item.get("price"),
            reason=reason,
            created_by=created_by,
        )


def restore_order_stock(
    order: Dict[str, Any],
    *,
    reason: str = "stock_restore",
    created_by: Optional[str] = None,
) -> None:
    """Increment product stock back for every line item on an order."""
    if not isinstance(order, dict):
        return
    restore_items(
        order.get("items"),
        order_id=order.get("id"),
        reason=reason,
        created_by=created_by,
    )


def hold_order_stock(
    order: Dict[str, Any],
    *,
    reason: str = "stock_hold",
    created_by: Optional[str] = None,
) -> None:
    """Decrement product stock for every line item.

    Mirror of :func:`restore_order_stock`, used when a previously released order
    (e.g. a failed payment the customer actually paid for) is revived to ``Paid``.
    Stock never drops below zero.
    """
    items = order.get("items")
    if not isinstance(items, list):
        return

    order_id = order.get("id")

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

        new_stock = max(0, current_stock - quantity)
        supabase.table("products").update(
            {"stock_quantity": new_stock}
        ).eq("id", product_id).execute()

        record_inventory_movement(
            product_id=product_id,
            order_id=order_id,
            change_qty=-(current_stock - new_stock),
            quantity_before=current_stock,
            quantity_after=new_stock,
            unit_price=item.get("price"),
            reason=reason,
            created_by=created_by,
        )


def release_stock_once(
    order: Dict[str, Any],
    new_status: str = "Payment Failed",
    *,
    created_by: Optional[str] = None,
) -> bool:
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

    reason = {
        "Cancelled": "cancel",
        "Refunded": "refund",
        "Payment Failed": "payment_failed",
    }.get(new_status, "stock_restore")
    restore_order_stock(order, reason=reason, created_by=created_by)
    return True
