import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from fastapi.staticfiles import StaticFiles


RASA_REST_URL = os.getenv(
    "RASA_REST_URL", "http://127.0.0.1:5005/webhooks/rest/webhook"
)

app = FastAPI(title="Rasa ↔ FastAPI Bridge")
app.mount("/images", StaticFiles(directory="images"), name="images")
# Conversations API routers
try:
    from backend.routes.conversations import router as conversations_router
    from backend.routes.otp import router as otp_router
    from backend.db.session import SessionLocal, Base, engine
    from backend.schemas.conversation import ConversationCreate
    from backend.services.conversation_service import save_conversation, get_conversations
    from backend.services.otp_service import is_phone_verified, generate_otp, verify_otp
    from backend.schemas.otp import OTPGenerateRequest, OTPVerifyRequest
    app.include_router(conversations_router, prefix="/api")
    app.include_router(otp_router, prefix="/api")

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
    is_phone_verified = None
    generate_otp = None
    verify_otp = None

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
    # If no phone number, do NOT call Rasa; ask for number first to enforce OTP later
    if not payload.phone_number:
        return {"sender_id": sender, "replies": [{"text": "Please enter your phone number to proceed."}]}

    # Handle OTP flow first when phone number provided; only talk to Rasa after verification
    if payload.phone_number and SessionLocal and save_conversation and ConversationCreate and is_phone_verified:
        db = SessionLocal()
        try:
            phone = payload.phone_number.strip()
            # If not verified yet, handle OTP in backend
            if not is_phone_verified(db, phone):
                # If user sent 6-digit number, treat it as OTP attempt
                if payload.text and payload.text.strip().isdigit() and len(payload.text.strip()) == 6 and verify_otp and OTPVerifyRequest:
                    resp = verify_otp(db, OTPVerifyRequest(phone_number=phone, otp_code=payload.text.strip()))
                    if resp.success:
                        # On success, fetch previous conversation and return it as messages, instruct user to continue
                        prev = get_conversations(db, phone)
                        rendered: list[dict] = []
                        if prev and prev.message:
                            for line in str(prev.message).split("\n"):
                                line = line.strip()
                                if not line:
                                    continue
                                if line.lower().startswith("user:"):
                                    rendered.append({"text": line.split(":",1)[1].strip()})
                                elif line.lower().startswith("bot:"):
                                    rendered.append({"text": line.split(":",1)[1].strip()})
                                else:
                                    rendered.append({"text": line})
                        rendered.append({"text": "OTP verified. You can continue chatting now."})
                        return {"sender_id": sender, "replies": rendered or [{"text":"OTP verified. Start chatting."}]}
                    else:
                        return {"sender_id": sender, "replies": [{"text": resp.message}]}
                # Otherwise, send/generate OTP prompt
                if generate_otp and OTPGenerateRequest:
                    _ = generate_otp(db, OTPGenerateRequest(phone_number=phone))
                return {"sender_id": sender, "replies": [{"text": "An OTP has been sent. Please enter the 6-digit code to proceed."}]}

            # If verified: proceed to send to Rasa below; we will persist after reply
        finally:
            db.close()

    # Only now talk to Rasa
    data = {"sender": sender, "message": payload.text}
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(RASA_REST_URL, json=data)
            r.raise_for_status()
            replies = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa unreachable: {e!s}")

    # Persist conversation if verified and services available
    if payload.phone_number and SessionLocal and save_conversation and ConversationCreate and is_phone_verified:
        db = SessionLocal()
        try:
            phone = payload.phone_number.strip()
            if is_phone_verified(db, phone):
                save_conversation(
                    db,
                    ConversationCreate(
                        phone_number=phone, role="user", message=payload.text
                    ),
                )
                for reply in replies:
                    if isinstance(reply, dict) and reply.get("text"):
                        save_conversation(
                            db,
                            ConversationCreate(
                                phone_number=phone,
                                role="bot",
                                message=reply["text"],
                            ),
                        )
        finally:
            db.close()

    return {"sender_id": sender, "replies": replies}


