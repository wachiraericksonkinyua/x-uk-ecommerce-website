import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"


async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 600,
    response_format: Optional[Dict[str, Any]] = None,
) -> str:
    """Call OpenRouter and return the assistant's text content.

    Shared by the storefront assistant (`routers/ai.py`) and the WhatsApp bot
    so there is a single place that talks to the LLM provider.
    """
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="AI is not configured")

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json=payload,
            timeout=60.0,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"AI provider error: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]
