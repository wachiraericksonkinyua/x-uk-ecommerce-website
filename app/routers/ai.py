import os
import httpx
from fastapi import APIRouter as FastAPIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.database import supabase
from app.dependencies import get_current_user
from dotenv import load_dotenv

load_dotenv()
router = FastAPIRouter(prefix="/ai", tags=["AI Assistant"])

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

@router.post("/chat")
async def chat_with_ai(payload: ChatRequest, current_user = Depends(get_current_user)):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    # 1. Get the latest user message and store it
    user_message = payload.messages[-1]
    supabase.table("chat_history").insert({
        "user_id": current_user.id,
        "role": "user",
        "content": user_message["content"]
    }).execute()

    # 2. Fetch active products for context
    products_res = supabase.table("products").select("name, price, brand, description").execute()
    product_rows = products_res.data or []
    inventory_lines = []
    for product in product_rows:
        if not isinstance(product, dict): continue
        name = product.get("name") or "Unknown"
        brand = product.get("brand") or "Unknown"
        price = product.get("price")
        if not isinstance(price, (int, float)): price = "0.00"
        description = product.get("description") or "No description"
        inventory_lines.append(f"- {name} ({brand}): ${price} - {description}")
    inventory_str = "\n".join(inventory_lines)

    system_prompt = f"""You are an expert, friendly salesperson assistant for X-UK, a phone retailer. 
    Your goal is to guide the user to the best phone recommendation based on their needs.

    Inventory:
    {inventory_str}

    Conversation Flow:
    1. If vague, ask brief qualifying questions (budget, use, brand) one at a time.
    2. When suggesting phones, you MUST provide the product_id so the UI can add it to the cart.
    3. Format your recommendations as a JSON object array for products:
       [
         {{"name": "iPhone 17", "product_id": "UUID", "reason": "Reason here"}},
         ...
       ]
    4. Keep text concise and use bullet points.
    5. Always end by asking if they need differences explained between iPhone and others."""

    # 3. Retrieve last 6 messages
    history_res = supabase.table("chat_history") \
        .select("role, content") \
        .eq("user_id", current_user.id) \
        .order("created_at", desc=True) \
        .limit(6) \
        .execute()
    # Reverse to get oldest first for AI context
    history = history_res.data[::-1]

    # 4. Construct messages for AI
    messages = [{"role": "system", "content": system_prompt}] + history

    # 5. Call AI
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "meta-llama/llama-3.1-8b-instruct", "messages": messages},
            timeout=30.0
        )
        
    if response.status_code != 200:
        error_detail = response.text
        raise HTTPException(status_code=500, detail=f"AI Service Error: {error_detail}")

    # 6. Store AI response
    ai_data = response.json()
    ai_content = ai_data["choices"][0]["message"]["content"]
    supabase.table("chat_history").insert({
        "user_id": current_user.id,
        "role": "assistant",
        "content": ai_content
    }).execute()

    return ai_data
