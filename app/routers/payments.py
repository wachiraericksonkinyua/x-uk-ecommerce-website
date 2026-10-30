from fastapi import APIRouter, Request
from app.services.mpesa import process_stk_callback

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/callback")
async def mpesa_callback(request: Request):
    """Canonical M-Pesa STK callback endpoint (configured as DARAJA_CALLBACK_URL)."""
    payload = await request.json()
    process_stk_callback(payload)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
