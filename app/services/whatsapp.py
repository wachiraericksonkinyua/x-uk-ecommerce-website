import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.database import supabase
from app.services.ai import chat_completion

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")
OWNER_WHATSAPP_NUMBER = os.environ.get("OWNER_WHATSAPP_NUMBER")
GRAPH_VERSION = os.environ.get("WHATSAPP_GRAPH_VERSION", "v20.0")

HISTORY_LIMIT = 8
HOT_THRESHOLD = int(os.environ.get("LEAD_HOT_THRESHOLD", "70"))
WARM_THRESHOLD = int(os.environ.get("LEAD_WARM_THRESHOLD", "40"))

TRIAGE_SYSTEM_PROMPT = """You are the friendly sales assistant for X-UK, a phone retailer in Kenya.
Your job is to qualify WhatsApp leads and move them toward a purchase.

Rules:
- Ask ONE qualifying question at a time (budget, preferred brand/model, timeline, location).
- Keep replies short, warm and WhatsApp-friendly. No markdown headings.
- Never invent stock. If unsure, offer to connect the customer with a human.

You MUST return ONLY a JSON object (no other text) with this shape:
{
  "reply": "the message to send to the customer",
  "intent": "browsing|price|purchase|support|other",
  "interest": "specific phone or null",
  "budget": number or null,
  "timeline": "now|this_week|later|null",
  "location": "string or null",
  "score": 0,
  "stage": "new|warm|hot|cold"
}
`score` is an integer 0-100 estimating how ready the customer is to buy
(budget clarity + product specificity + urgency)."""


# --------------------------------------------------------------------------- #
# Webhook security
# --------------------------------------------------------------------------- #
def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """Validate Meta's `X-Hub-Signature-256` header against the app secret.

    Meta signs the raw request body with HMAC-SHA256 using your app secret.
    If `WHATSAPP_APP_SECRET` is not configured we allow the request (local dev),
    but in production it MUST be set so unsigned requests are rejected.
    """
    app_secret = os.environ.get("WHATSAPP_APP_SECRET")
    if not app_secret:
        print("[whatsapp] WHATSAPP_APP_SECRET not set; skipping signature check")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    # constant-time comparison to avoid timing attacks
    return hmac.compare_digest(expected, provided)


# --------------------------------------------------------------------------- #
# WhatsApp Cloud API
# --------------------------------------------------------------------------- #
async def send_whatsapp_message(to: str, body: str) -> bool:
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("[whatsapp] not configured; skipping outbound send")
        return False

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            url,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
            json=payload,
            timeout=30.0,
        )
    if res.status_code >= 300:
        print(f"[whatsapp] send failed {res.status_code}: {res.text}")
        return False
    return True


def extract_inbound_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Pull the first text message out of a Meta webhook payload."""
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages") or []
        if not messages:
            return None
        message = messages[0]

        name = None
        contacts = value.get("contacts") or []
        if contacts:
            name = (contacts[0].get("profile") or {}).get("name")

        text = ""
        if message.get("type") == "text":
            text = (message.get("text") or {}).get("body", "")

        return {
            "from": message.get("from"),
            "text": text,
            "id": message.get("id"),
            "name": name,
        }
    except (KeyError, IndexError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Lead persistence
# --------------------------------------------------------------------------- #
def get_or_create_lead(phone: str, name: Optional[str] = None) -> Dict[str, Any]:
    res = supabase.table("leads").select("*").eq("phone", phone).execute()
    if res.data:
        lead = res.data[0]
        if name and not lead.get("name"):
            supabase.table("leads").update({"name": name}).eq("id", lead["id"]).execute()
            lead["name"] = name
        return lead

    inserted = (
        supabase.table("leads")
        .insert({"phone": phone, "name": name, "source": "whatsapp"})
        .execute()
    )
    return inserted.data[0]


def log_message(lead_id: str, direction: str, body: str, wa_message_id: Optional[str] = None) -> None:
    supabase.table("whatsapp_messages").insert({
        "lead_id": lead_id,
        "direction": direction,
        "body": body,
        "wa_message_id": wa_message_id,
    }).execute()


def fetch_history(lead_id: str, limit: int = HISTORY_LIMIT) -> List[Dict[str, Any]]:
    res = (
        supabase.table("whatsapp_messages")
        .select("direction, body")
        .eq("lead_id", lead_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(res.data or []))


def _status_from_score(score: int) -> str:
    if score >= HOT_THRESHOLD:
        return "hot"
    if score >= WARM_THRESHOLD:
        return "warm"
    return "cold"


def _apply_meta(lead_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    update: Dict[str, Any] = {
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        score = int(meta.get("score"))
        score = max(0, min(100, score))
        update["score"] = score
        update["status"] = _status_from_score(score)
    except (TypeError, ValueError):
        pass

    for field in ("interest", "timeline", "location", "budget"):
        value = meta.get(field)
        if value not in (None, "", "null"):
            update[field] = value

    supabase.table("leads").update(update).eq("id", lead_id).execute()
    return update


def _parse_model_output(raw: str):
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            data = json.loads(text[start:end + 1])
            reply = str(data.get("reply") or "").strip()
            if reply:
                return reply, data
        except json.JSONDecodeError:
            pass
    return text, {}


async def _notify_owner(lead: Dict[str, Any], meta: Dict[str, Any]) -> None:
    if not OWNER_WHATSAPP_NUMBER:
        return
    summary = (
        f"🔥 HOT LEAD\n"
        f"Name: {lead.get('name') or 'Unknown'}\n"
        f"Phone: {lead.get('phone')}\n"
        f"Interest: {meta.get('interest') or '-'}\n"
        f"Budget: {meta.get('budget') or '-'}\n"
        f"Score: {meta.get('score')}\n"
        f"Timeline: {meta.get('timeline') or '-'}"
    )
    await send_whatsapp_message(OWNER_WHATSAPP_NUMBER, summary)


# --------------------------------------------------------------------------- #
# Main entry point (called from the webhook in a background task)
# --------------------------------------------------------------------------- #
async def handle_inbound_message(payload: Dict[str, Any]) -> None:
    try:
        message = extract_inbound_message(payload)
        if not message or not message.get("from"):
            return

        phone = message["from"]
        text = message.get("text") or ""
        lead = get_or_create_lead(phone, message.get("name"))
        log_message(lead["id"], "inbound", text, message.get("id"))

        history = fetch_history(lead["id"])
        messages = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
        for row in history:
            messages.append({
                "role": "user" if row.get("direction") == "inbound" else "assistant",
                "content": row.get("body", ""),
            })

        raw = await chat_completion(messages, temperature=0.4, max_tokens=500)
        reply, meta = _parse_model_output(raw)

        log_message(lead["id"], "outbound", reply)

        was_hot = lead.get("status") == "hot"
        updated = _apply_meta(lead["id"], meta)

        await send_whatsapp_message(phone, reply)

        if updated.get("status") == "hot" and not was_hot:
            await _notify_owner(lead, meta)
    except Exception as e:  # background task: never crash the worker
        print(f"[whatsapp] handle_inbound_message error: {e}")
