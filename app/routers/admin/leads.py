from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import supabase
from app.services.whatsapp import log_message, send_whatsapp_message
from app.utils.pagination import page_range

router = APIRouter(prefix="/leads", tags=["Admin · Leads"])

VALID_STATUSES = {"new", "warm", "hot", "cold", "won", "lost"}


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    interest: Optional[str] = None
    budget: Optional[float] = None
    location: Optional[str] = None
    timeline: Optional[str] = None
    assigned_to: Optional[str] = None


class LeadReply(BaseModel):
    message: str


@router.get("/stats")
def lead_stats():
    """Funnel counts by status + hottest open leads."""
    try:
        res = supabase.table("leads").select("status, score").execute()
        leads = res.data or []
        counts = {status: 0 for status in VALID_STATUSES}
        for lead in leads:
            if not isinstance(lead, dict):
                continue
            status = lead.get("status")
            if status in counts:
                counts[status] += 1

        hot_res = (
            supabase.table("leads")
            .select("id, name, phone, interest, score, status, last_message_at")
            .eq("status", "hot")
            .order("score", desc=True)
            .limit(10)
            .execute()
        )
        return {
            "success": True,
            "total": len(leads),
            "by_status": counts,
            "hot_leads": hot_res.data or [],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_leads(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Name or phone"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        query = supabase.table("leads").select("*", count="exact")
        if status:
            query = query.eq("status", status)
        if search:
            term = search.replace(",", "").strip()
            query = query.or_(f"name.ilike.%{term}%,phone.ilike.%{term}%")
        start, end = page_range(page, page_size)
        response = query.order("last_message_at", desc=True).range(start, end).execute()
        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total": response.count if response.count is not None else len(response.data or []),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lead_id}")
def get_lead(lead_id: str):
    try:
        response = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{lead_id}/messages")
def get_lead_messages(lead_id: str):
    try:
        response = (
            supabase.table("whatsapp_messages")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at")
            .execute()
        )
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lead_id}")
def update_lead(lead_id: str, payload: LeadUpdate):
    data = payload.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "status" in data and data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(VALID_STATUSES)}")
    if "score" in data and data["score"] is not None:
        data["score"] = max(0, min(100, data["score"]))
    try:
        response = supabase.table("leads").update(data).eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/reply")
async def reply_to_lead(lead_id: str, payload: LeadReply):
    """Send a manual WhatsApp message and record it in the transcript."""
    try:
        lead_res = supabase.table("leads").select("phone").eq("id", lead_id).single().execute()
        lead = lead_res.data
        if not isinstance(lead, dict):
            raise HTTPException(status_code=404, detail="Lead not found")

        sent = await send_whatsapp_message(lead["phone"], payload.message)
        log_message(lead_id, "outbound", payload.message)

        return {
            "success": True,
            "delivered": sent,
            "message": "Reply sent" if sent else "Reply stored but WhatsApp delivery failed",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/assign")
def assign_lead(lead_id: str, assigned_to: Optional[str] = Query(None)):
    try:
        response = (
            supabase.table("leads")
            .update({"assigned_to": assigned_to})
            .eq("id", lead_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
