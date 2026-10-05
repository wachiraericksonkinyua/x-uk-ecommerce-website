import uuid
from typing import Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.routers.daraja_service import DarajaService

router = APIRouter(prefix="/orders", tags=["orders"])


def _coerce_stock_quantity(value: object, item_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise HTTPException(status_code=400, detail=f"Missing or invalid stock quantity for {item_name}")

    if not isinstance(value, (str, int, float)):
        raise HTTPException(status_code=400, detail=f"Invalid stock quantity for {item_name}")

    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid stock quantity for {item_name}")


class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    qty: int
    image: Optional[str] = ""

class CheckoutRequest(BaseModel):
    phone: str
    fulfillment: str
    location: str
    delivery_address: str = ""
    payment_method: str
    items: List[OrderItem]
    total: float
    customer_id: Optional[str] = None

@router.post("/checkout", status_code=201)
async def process_checkout(payload: CheckoutRequest):
    try:
        # 1. Validate stock first
        for item in payload.items:
            prod_res = supabase.table("products").select("stock_quantity").eq("id", item.id).execute()
            if not prod_res.data:
                raise HTTPException(status_code=404, detail=f"Product {item.id} not found")

            product_row = prod_res.data[0]
            if not isinstance(product_row, dict):
                raise HTTPException(status_code=500, detail=f"Invalid stock data for product {item.id}")

            stock_quantity = product_row.get("stock_quantity")
            validated_stock = _coerce_stock_quantity(stock_quantity, item.name)

            if validated_stock < item.qty:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}")

        order_uuid = str(uuid.uuid4())
        short_ref = f"GWV-{order_uuid[:4]}"
        checkout_request_id = ""

        # 2. Decrement product stock quantities
        for item in payload.items:
            prod_res = supabase.table("products").select("stock_quantity").eq("id", item.id).execute()
            if not prod_res.data:
                raise HTTPException(status_code=404, detail=f"Product {item.id} not found")

            product_row = prod_res.data[0]
            if not isinstance(product_row, dict):
                raise HTTPException(status_code=500, detail=f"Invalid stock data for product {item.id}")

            current_stock = product_row.get("stock_quantity")
            validated_current_stock = _coerce_stock_quantity(current_stock, item.name)

            new_stock = max(0, validated_current_stock - item.qty)
            supabase.table("products").update({"stock_quantity": new_stock}).eq("id", item.id).execute()

        # 3. Trigger M-Pesa STK Push
        if "M-Pesa" in payload.payment_method:
            daraja = DarajaService()
            stk_response = await daraja.send_stk_push(
                phone_number=payload.phone,
                amount=int(payload.total),
                account_reference=short_ref,
                transaction_desc=f"Payment for order {short_ref}"
            )
            # Use the actual CheckoutRequestID from M-Pesa if available, otherwise fallback
            checkout_request_id = stk_response.get("CheckoutRequestID", f"sim_{short_ref}")

        order_record = {
            "id": order_uuid,
            "order_reference": short_ref,
            "checkout_request_id": checkout_request_id,
            "customer_phone": payload.phone,
            "fulfillment": payload.fulfillment,
            "location": payload.location,
            "delivery_address": (payload.delivery_address or "").strip(),
            "payment_method": payload.payment_method,
            "total_amount": payload.total,
            "status": "Pending PIN" if "M-Pesa" in payload.payment_method else "Processing",
            "items": [item.dict() for item in payload.items]
        }

        # 2. Save order to Supabase database
        supabase.table("orders").insert(order_record).execute()

        return {
            "status": "success",
            "message": "STK prompt sent to phone",
            "order_id": short_ref,
            "checkout_request_id": checkout_request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))