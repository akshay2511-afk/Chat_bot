import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

RASA_REST_URL = os.getenv(
    "RASA_REST_URL", "http://127.0.0.1:5005/webhooks/rest/webhook"
)

app = FastAPI(title="Rasa ↔ FastAPI Bridge")

class ChatIn(BaseModel):
    text: str
    sender_id: Optional[str] = None  # keep stable per user/session


class ChatOut(BaseModel):
    sender_id: str
    replies: List[Dict[str, Any]]  # Rasa returns list of messages (text/image/buttons/...)


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://127.0.0.1:5005/health")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa health check failed: {e!s}")


@app.post("/chat", response_model=ChatOut)
async def chat(payload: ChatIn):
    sender = payload.sender_id or str(uuid.uuid4())
    data = {"sender": sender, "message": payload.text}
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(RASA_REST_URL, json=data)
            r.raise_for_status()
            replies = r.json()  # e.g. [{"recipient_id":"...", "text":"..."}, {"image":"..."}, ...]
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa unreachable: {e!s}")
    return {"sender_id": sender, "replies": replies}

