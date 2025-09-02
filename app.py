import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

RASA_REST_URL = os.getenv(
    "RASA_REST_URL", "http://127.0.0.1:5005/webhooks/rest/webhook"
)

app = FastAPI(title="Rasa ↔ FastAPI Bridge")

# Conversations API routers
try:
    from backend.routes.conversations import router as conversations_router
    from backend.db.session import SessionLocal, Base, engine
    from backend.schemas.conversation import ConversationCreate
    from backend.services.conversation_service import save_conversation
    app.include_router(conversations_router, prefix="/api")

    @app.on_event("startup")
    def ensure_tables_created() -> None:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            # If DB not reachable or PAN DB missing, we ignore here; errors will surface on use.
            pass
except Exception as _:
    SessionLocal = None
    save_conversation = None
    ConversationCreate = None

class ChatIn(BaseModel):
    text: str
    sender_id: Optional[str] = None  # keep stable per user/session
    phone_number: Optional[str] = None  # when provided, will be used to persist messages


class ChatOut(BaseModel):
    sender_id: str
    replies: List[Dict[str, Any]]  # Rasa returns list of messages (text/image/buttons/...)


@app.get("/", response_class=FileResponse)
def root():
    index_path = os.path.join(os.path.dirname(__file__), "chat.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="chat.html not found")
    return FileResponse(index_path, media_type="text/html")


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
            replies = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa unreachable: {e!s}")

    # Persist conversation if a phone number is provided and services are available
    if payload.phone_number and SessionLocal and save_conversation and ConversationCreate:
        db = SessionLocal()
        try:
            # save user message
            save_conversation(
                db,
                ConversationCreate(
                    phone_number=payload.phone_number, role="user", message=payload.text
                ),
            )
            # save each bot text reply
            for reply in replies:
                if isinstance(reply, dict) and reply.get("text"):
                    save_conversation(
                        db,
                        ConversationCreate(
                            phone_number=payload.phone_number,
                            role="bot",
                            message=reply["text"],
                        ),
                    )
        finally:
            db.close()

    return {"sender_id": sender, "replies": replies}

