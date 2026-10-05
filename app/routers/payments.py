from fastapi import APIRouter, Request
from app.database import supabase

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/callback")
async def mpesa_callback(request: Request):
    data = await request.json()
    stk_callback = data.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_request_id = stk_callback.get("CheckoutRequestID")

    if result_code == 0:
        meta_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        receipt = next((i.get("Value") for i in meta_items if i.get("Name") == "MpesaReceiptNumber"), "MPESA_PAID")

        supabase.table("orders").update({
            "status": "Paid",
            "receipt_number": receipt
        }).eq("checkout_request_id", checkout_request_id).execute()

    elif result_code == 1032:
        supabase.table("orders").update({
            "status": "Cancelled"
        }).eq("checkout_request_id", checkout_request_id).execute()

    else:
        supabase.table("orders").update({
            "status": "Payment Failed"
        }).eq("checkout_request_id", checkout_request_id).execute()

    return {"ResultCode": 0, "ResultDesc": "Accepted"}