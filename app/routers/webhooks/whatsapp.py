import json
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.services.whatsapp import handle_inbound_message, verify_signature

router = APIRouter(prefix="/webhooks/whatsapp", tags=["Webhooks · WhatsApp"])

WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")


@router.get("")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta calls this once to confirm we own the webhook URL."""
    if hub_mode == "subscribe" and WHATSAPP_VERIFY_TOKEN and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge or "")
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive messages. Verify the signature, ack fast, process in the background."""
    raw_body = await request.body()

    # Reject anything not signed by Meta's app secret (when configured).
    if not verify_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    background_tasks.add_task(handle_inbound_message, payload)
    return {"status": "received"}
