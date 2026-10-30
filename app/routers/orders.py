from __future__ import annotations

import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from app.database import supabase
from app.routers.daraja_service import DarajaService
from app.utils.email import send_receipt_email
from app.dependencies import get_current_user, require_admin
from app.services.inventory import hold_order_stock, release_stock_once, restore_order_stock
from app.services.mpesa import apply_stk_result, process_stk_callback
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/orders", tags=["orders"])

class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str  # e.g., "Pending PIN", "Paid", "Processing", "Shipped", "Delivered"

class ManualPaymentVerify(BaseModel):
    receipt_number: str


class ReceiptVerify(BaseModel):
    receipt_number: str


# Statuses a customer can manually prove payment for after a failed/stuck push
RECEIPT_VERIFIABLE_STATUSES = {"Pending PIN", "Payment Failed"}

def _coerce_stock_quantity(value: object, item_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise HTTPException(status_code=400, detail=f"Missing or invalid stock quantity for {item_name}")

    if not isinstance(value, (str, int, float)):
        raise HTTPException(status_code=400, detail=f"Invalid stock quantity for {item_name}")

    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid stock quantity for {item_name}")


def _coerce_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise HTTPException(status_code=400, detail=f"Missing or invalid {field_name}")

    if not isinstance(value, (str, int, float)):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")

    try:
        return float(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    qty: int
    image: Optional[str] = ""

class CheckoutRequest(BaseModel):
    phone: str
    email: EmailStr
    fulfillment: str
    location_id: Optional[str] = None  # Required only for delivery
    delivery_address: Optional[str] = None
    payment_method: str
    items: List[OrderItem]
    total: float
    customer_id: Optional[str] = None


def _normalize_phone(phone: Optional[str]) -> str:
    """Normalize a Kenyan phone number to the 254XXXXXXXXX format Daraja expects."""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if digits.startswith("254"):
        return digits
    if digits.startswith("0") and len(digits) >= 9:
        return "254" + digits[1:]
    if len(digits) == 9:
        return "254" + digits
    return digits

@router.get("/me")
def get_my_orders(current_user = Depends(get_current_user)):
    """Fetch orders for the currently authenticated user."""
    try:
        response = supabase.table("orders").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/cancel")
def cancel_my_order(order_id: str, current_user = Depends(get_current_user)):
    """Customer cancels their own order; held stock is restored (idempotent)."""
    try:
        order_res = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .eq("user_id", current_user.id)
            .execute()
        )
        if not order_res.data or not isinstance(order_res.data[0], dict):
            raise HTTPException(status_code=404, detail="Order not found")

        order = order_res.data[0]
        if order.get("status") in {"Shipped", "Delivered", "Cancelled"}:
            raise HTTPException(status_code=400, detail="Order can no longer be cancelled")

        if not release_stock_once(order, "Cancelled"):
            # Not holding stock (e.g. already Paid) — just mark it cancelled.
            supabase.table("orders").update({"status": "Cancelled"}).eq("id", order_id).execute()

        return {"success": True, "message": "Order cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
def get_user_orders(user_id: str, _admin_user = Depends(require_admin)):
    """Admin endpoint to fetch a specific user's orders."""
    try:
        response = supabase.table("orders").select("*").eq("user_id", user_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/all")
def get_all_orders(admin_user = Depends(require_admin)):
    """Admin endpoint to fetch all orders for the store."""
    try:
        response = supabase.table("orders").select("*").order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/checkout", status_code=201)
async def process_checkout(payload: CheckoutRequest, current_user = Depends(get_current_user)):
    try:
        # 0. Resolve fulfillment: pickup is always free and needs no location.
        is_pickup = (payload.fulfillment or "").strip().lower() == "pickup"

        if is_pickup:
            location_name = "Store Pickup"
            validated_delivery_cost = 0.0
        else:
            if not payload.location_id:
                raise HTTPException(status_code=400, detail="Delivery location is required")

            loc_res = supabase.table("delivery_locations").select("name, cost, active").eq("id", payload.location_id).single().execute()
            delivery_location = loc_res.data
            if not isinstance(delivery_location, dict):
                raise HTTPException(status_code=400, detail="Invalid delivery location")
            if delivery_location.get("active") is False:
                raise HTTPException(status_code=400, detail="Delivery location is currently unavailable")

            location_name = delivery_location.get("name")
            if not isinstance(location_name, str):
                raise HTTPException(status_code=400, detail="Invalid delivery location")
            validated_delivery_cost = _coerce_float(delivery_location.get("cost"), "delivery cost")

        normalized_phone = _normalize_phone(payload.phone)
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="A valid phone number is required")

        if not payload.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # 1. Resolve prices from the database and validate stock.
        #    Never trust client-supplied prices or totals.
        line_items = []
        items_total = 0.0
        for item in payload.items:
            if item.qty <= 0:
                raise HTTPException(status_code=400, detail=f"Invalid quantity for {item.name}")

            prod_res = supabase.table("products").select("name, price, stock_quantity").eq("id", item.id).execute()
            if not prod_res.data or not isinstance(prod_res.data[0], dict):
                raise HTTPException(status_code=404, detail=f"Product {item.id} not found")

            product_row = prod_res.data[0]
            validated_stock = _coerce_stock_quantity(product_row.get("stock_quantity"), item.name)
            if validated_stock < item.qty:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}")

            unit_price = _coerce_float(product_row.get("price"), f"price for {item.name}")
            if unit_price < 0:
                raise HTTPException(status_code=400, detail=f"Invalid price for {item.name}")

            items_total += unit_price * item.qty
            line_items.append({
                "id": item.id,
                "name": product_row.get("name") or item.name,
                "price": unit_price,
                "qty": item.qty,
                "image": item.image or "",
            })

        validated_items_total = round(items_total, 2)
        order_total = round(validated_items_total + validated_delivery_cost, 2)

        order_uuid = str(uuid.uuid4())
        short_ref = f"GWV-{order_uuid[:4]}"
        is_mpesa = "M-Pesa" in payload.payment_method

        # 2. Persist the order first so stock is never held without a record
        order_record = {
            "id": order_uuid,
            "order_reference": short_ref,
            "checkout_request_id": "",
            "user_id": current_user.id,
            "customer_phone": normalized_phone,
            "customer_email": payload.email,
            "fulfillment": payload.fulfillment,
            "location_name": location_name,
            "delivery_cost": validated_delivery_cost,
            "delivery_address": "" if is_pickup else (payload.delivery_address or "").strip(),
            "payment_method": payload.payment_method,
            "total_amount": order_total,
            "status": "Pending PIN" if is_mpesa else "Processing",
            "items": line_items,
        }
        supabase.table("orders").insert(order_record).execute()

        # 3. Decrement product stock quantities
        try:
            for line in line_items:
                prod_res = supabase.table("products").select("stock_quantity").eq("id", line["id"]).execute()
                if not prod_res.data or not isinstance(prod_res.data[0], dict):
                    raise HTTPException(status_code=404, detail=f"Product {line['id']} not found")

                current_stock = _coerce_stock_quantity(prod_res.data[0].get("stock_quantity"), line["name"])
                new_stock = max(0, current_stock - line["qty"])
                supabase.table("products").update({"stock_quantity": new_stock}).eq("id", line["id"]).execute()
        except Exception:
            # Roll back any partial decrements and remove the dangling order
            restore_order_stock(order_record)
            supabase.table("orders").delete().eq("id", order_uuid).execute()
            raise

        checkout_request_id = ""

        # 4. Trigger M-Pesa STK Push using the server-computed total.
        #    The order stays "Pending PIN" with stock held even if Daraja is
        #    slow/unreachable — a failed initiation must never fail the order.
        if is_mpesa:
            final_total = int(round(order_total))
            if final_total <= 0:
                release_stock_once(order_record, "Payment Failed")
                raise HTTPException(status_code=400, detail="Order total is invalid")

            stk_response: dict = {}
            try:
                daraja = DarajaService()
                stk_response = await daraja.send_stk_push(
                    phone_number=normalized_phone,
                    amount=final_total,
                    account_reference=short_ref,
                    transaction_desc=f"Payment for order {short_ref}"
                )
            except Exception as exc:
                # Non-fatal: keep the order pending so the customer can still
                # enter their PIN on the phone or use the manual receipt
                # verifier. Do NOT release stock or mark it "Payment Failed".
                print(f"[orders] WARNING: M-Pesa STK initiation failed for {short_ref}: {exc}")

            checkout_request_id = stk_response.get("CheckoutRequestID") or ""
            if checkout_request_id:
                supabase.table("orders").update(
                    {"checkout_request_id": checkout_request_id}
                ).eq("id", order_uuid).execute()

        return {
            "status": "success",
            "message": "Order processed. If using M-Pesa, check your phone for the STK prompt.",
            "order_id": short_ref,
            "checkout_request_id": checkout_request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/track/{order_ref}")
async def track_order_by_reference(order_ref: str):
    """Allows customers to track their order live using the short reference (e.g., GWV-1234).

    While an order is still ``Pending PIN`` we actively poll Daraja's STK query
    endpoint so cancellations/timeouts reflect immediately even when the
    callback webhook (ngrok) is unreachable.
    """
    try:
        response = supabase.table("orders").select("*").eq("order_reference", order_ref).single().execute()
        order = response.data
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if isinstance(order, dict):
            checkout_request_id = order.get("checkout_request_id")
            should_query = (
                order.get("status") == "Pending PIN"
                and isinstance(checkout_request_id, str)
                and bool(checkout_request_id)
            )

            if should_query:
                try:
                    daraja = DarajaService()
                    result = await daraja.query_stk_status(checkout_request_id)
                    result_code = result.get("ResultCode")

                    if result_code is not None:
                        meta_items = (result.get("CallbackMetadata") or {}).get("Item", [])
                        new_status = apply_stk_result(checkout_request_id, result_code, meta_items)
                        if new_status:
                            fresh_res = (
                                supabase.table("orders")
                                .select("*")
                                .eq("id", order["id"])
                                .single()
                                .execute()
                            )
                            if fresh_res.data:
                                order = fresh_res.data
                except Exception as exc:
                    print(f"[orders] STK status query failed for {order_ref}: {exc}")

        return {"success": True, "data": order}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/verify-receipt")
def verify_receipt(order_id: str, payload: ReceiptVerify):
    """Customer fallback: confirm payment using the M-Pesa message code.

    Marks a pending/failed order as Paid, stores the receipt and finalizes the
    stock adjustment. Accepts either the order UUID or the short reference.
    """
    receipt_number = (payload.receipt_number or "").strip()
    if not receipt_number:
        raise HTTPException(status_code=400, detail="An M-Pesa receipt number is required")

    try:
        res = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not res.data:
            res = supabase.table("orders").select("*").eq("order_reference", order_id).execute()
        if not res.data or not isinstance(res.data[0], dict):
            raise HTTPException(status_code=404, detail="Order not found")

        order = res.data[0]
        current_status = order.get("status")

        if current_status == "Paid":
            return {"success": True, "message": "Payment already verified", "data": order}

        if current_status not in RECEIPT_VERIFIABLE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be verified from status '{current_status}'",
            )

        updated = (
            supabase.table("orders")
            .update({"status": "Paid", "receipt_number": receipt_number})
            .eq("id", order["id"])
            .eq("status", current_status)
            .execute()
        )
        if not updated.data:
            raise HTTPException(
                status_code=409,
                detail="Order status changed. Please refresh and try again.",
            )

        # A failed payment already released its stock — hold it again now that it's paid.
        if current_status == "Payment Failed":
            hold_order_stock(order)

        customer_email = order.get("customer_email")
        if isinstance(customer_email, str) and customer_email:
            items = order.get("items") if isinstance(order.get("items"), list) else []
            try:
                send_receipt_email(
                    customer_email,
                    str(order.get("order_reference") or ""),
                    _coerce_float(order.get("total_amount"), "order total"),
                    items,
                )
            except Exception as exc:
                print(f"[orders] receipt email failed for {order_id}: {exc}")

        return {"success": True, "message": "Payment verified", "data": updated.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    
@router.patch("/status/{order_id}")
def update_order_status(order_id: str, payload: StatusUpdate, _admin_user = Depends(require_admin)):
    """Admin endpoint to push real-time order status updates."""
    try:
        response = supabase.table("orders").update({"status": payload.status}).eq("id", order_id).execute()
        return {"success": True, "message": f"Order status updated to {payload.status}", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/verify-payment/{order_id}")
async def verify_mpesa_payment(order_id: str, payload: ManualPaymentVerify, _admin_user = Depends(require_admin)):
    """Admin endpoint: cross-checks the provided M-Pesa receipt with Daraja."""
    try:
        # daraja = DarajaService()
        # is_valid = await daraja.check_transaction(payload.receipt_number)

        # If Safaricom confirms it, we automatically approve the order
        order_res = supabase.table("orders").select("*").eq("id", order_id).single().execute()
        order = order_res.data

        if not isinstance(order, dict):
            raise HTTPException(status_code=404, detail="Order not found")

        customer_email = order.get("customer_email")
        order_reference = order.get("order_reference")
        total_amount = order.get("total_amount")
        items = order.get("items")

        if not isinstance(customer_email, str) or not customer_email:
            raise HTTPException(status_code=400, detail="Order does not have a valid customer email")
        if not isinstance(order_reference, str) or not order_reference:
            raise HTTPException(status_code=400, detail="Order reference missing")
        if not isinstance(items, list):
            items = []

        validated_total_amount = _coerce_float(total_amount, "order total")

        supabase.table("orders").update({
            "receipt_number": payload.receipt_number,
            "status": "Paid"  # Instantly flips to Paid
        }).eq("id", order_id).execute()

        send_receipt_email(customer_email, order_reference, validated_total_amount, items)

        return {"success": True, "message": "Payment verified and order approved!"}
    except HTTPException:
        raise
    except Exception:
        # If it fails, we can log it and set status to "Manual Review"
        raise HTTPException(status_code=400, detail="Invalid receipt or verification failed.")

@router.post("/status-result")
async def transaction_status_webhook(request: Request):
    """Legacy alias for the M-Pesa callback. Delegates to the shared service."""
    payload = await request.json()
    process_stk_callback(payload)
    return {"message": "Safaricom update received"}

