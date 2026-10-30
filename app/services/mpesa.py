from typing import Any, Dict, Optional

from app.database import supabase
from app.services.inventory import release_stock_once
from app.utils.email import send_receipt_email


def _safe_total(value: Any) -> float:
    try:
        if isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_result_code(value: Any) -> Optional[str]:
    """Daraja mixes ints and strings for ResultCode; normalize to a string."""
    if value is None:
        return None
    code = str(value).strip()
    return code or None


def _extract_receipt(meta_items: Any) -> Optional[str]:
    """Pull the MpesaReceiptNumber out of CallbackMetadata.Item if present."""
    if not isinstance(meta_items, list):
        return None
    for item in meta_items:
        if isinstance(item, dict) and item.get("Name") == "MpesaReceiptNumber":
            value = item.get("Value")
            if value:
                return str(value)
    return None


def _find_order(checkout_request_id: str) -> Optional[Dict[str, Any]]:
    res = (
        supabase.table("orders")
        .select("*")
        .eq("checkout_request_id", checkout_request_id)
        .execute()
    )
    if res.data and isinstance(res.data[0], dict):
        return res.data[0]
    return None


def _send_receipt(order: Dict[str, Any]) -> None:
    try:
        customer_email = order.get("customer_email")
        if not isinstance(customer_email, str) or not customer_email:
            return
        items = order.get("items", [])
        if not isinstance(items, list):
            items = []
        send_receipt_email(
            customer_email,
            str(order.get("order_reference", "")),
            _safe_total(order.get("total_amount")),
            items,
        )
    except Exception as exc:  # never let email failure undo a payment
        print(f"[mpesa] receipt email failed for {order.get('order_reference')}: {exc}")


def apply_stk_result(
    checkout_request_id: Optional[str],
    result_code: Any,
    callback_metadata: Any = None,
) -> str:
    """Reconcile a single STK result against its order.

    This is the single source of truth shared by the webhook callback and the
    tracking poll, so both paths behave identically:

      * ``ResultCode`` ``"0"`` / ``0`` -> atomically flip the order to ``Paid``
        and store the receipt (emailing it once).
      * ``1032`` -> release held stock and mark ``Cancelled``.
      * any other final code -> release held stock and mark ``Payment Failed``.

    Returns the resulting status, or ``""`` when the result is incomplete or
    nothing changed. The success transition is guarded so a stale/duplicate
    result can never overwrite an order that is already ``Paid``.
    """
    code = _normalize_result_code(result_code)
    if not checkout_request_id or code is None:
        return ""

    order = _find_order(checkout_request_id)
    if not order:
        return ""

    if code == "0":
        update: Dict[str, Any] = {"status": "Paid"}
        receipt = _extract_receipt(callback_metadata)
        if receipt:
            update["receipt_number"] = receipt

        # Atomic + idempotent: only transition orders that aren't already Paid.
        res = (
            supabase.table("orders")
            .update(update)
            .eq("checkout_request_id", checkout_request_id)
            .neq("status", "Paid")
            .execute()
        )
        if res.data:
            _send_receipt({**order, **update})
        return "Paid"

    new_status = "Cancelled" if code == "1032" else "Payment Failed"
    if release_stock_once(order, new_status):
        print(f"[mpesa] Released stock for order {checkout_request_id} ({new_status})")
    return new_status


def process_stk_callback(payload: Dict[str, Any]) -> None:
    """Entry point for M-Pesa STK Push callback webhooks."""
    try:
        body = payload.get("Body", {}).get("stkCallback", {})
        checkout_request_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")
        meta_items = (body.get("CallbackMetadata") or {}).get("Item", [])

        apply_stk_result(checkout_request_id, result_code, meta_items)
    except Exception as e:
        print(f"CRITICAL ERROR processing M-Pesa callback: {e}")
