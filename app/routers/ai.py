from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.database import supabase

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

@router.post("/chat")
async def store_ai_chat(payload: ChatRequest):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    # Fetch active products to give the AI live context of our stock
    products_res = supabase.table("products").select("name, price, brand, color, description").execute()
    inventory = products_res.data

    # Here is where we plug in our LLM logic using our live stock data
    return {
        "success": True, 
        "reply": f"Hello! I am your X-UK assistant. We currently have {len(inventory)} items in stock. How can I help you find the right phone today?"
    }