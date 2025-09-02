import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx


RASA_REST_URL = os.getenv(
    "RASA_REST_URL", "http://127.0.0.1:5005/webhooks/rest/webhook"
)

router = APIRouter()


class ChatIn(BaseModel):
    text: str
    sender_id: Optional[str] = None  # keep stable per user/session


class ChatOut(BaseModel):
    sender_id: str
    replies: List[Dict[str, Any]]  # Rasa returns list of messages (text/image/buttons/...)


@router.get("/", response_class=FileResponse)
def root():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    index_path = os.path.join(base_dir, "templates", "templates/chat.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="templates/chat.html not found")
    return FileResponse(index_path, media_type="text/html")


@router.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://127.0.0.1:5005/health")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa health check failed: {e!s}")


@router.post("/chat", response_model=ChatOut)
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


