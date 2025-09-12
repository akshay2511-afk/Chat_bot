import os
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
    from backend.routes.feedback import router as feedback_router
    from backend.routes.consent import router as consent_router
    from backend.routes.pan import router as pan_router
    from backend.routes.tan import router as tan_router
    from backend.db.session import SessionLocal, Base, engine
    from backend.schemas.conversation import ConversationCreate
    from backend.services.conversation_service import save_conversation, get_conversations, ensure_phone_number
    from backend.services.otp_service import is_phone_verified, generate_otp, verify_otp
    from backend.services.token_service import acquire_token, release_token
    from backend.services.history_service import append_session_history, append_number_history
    from backend.models.history import SessionChatHistory
    from backend.schemas.otp import OTPGenerateRequest, OTPVerifyRequest
    from backend.services.consent_service import seed_default_policies
    from backend.services.tan_service import save_tan_number
    from backend.schemas.conversation import SaveTANRequest
    app.include_router(conversations_router, prefix="/api")
    app.include_router(otp_router, prefix="/api")
    app.include_router(feedback_router, prefix="/api")
    app.include_router(consent_router, prefix="/api")
    app.include_router(pan_router, prefix="/api")
    app.include_router(tan_router, prefix="/api")

    @app.on_event("startup")
    def ensure_tables_created() -> None:
        try:
            Base.metadata.create_all(bind=engine)
            # Seed default consent policies
            db = SessionLocal()
            try:
                seed_default_policies(db)
            finally:
                db.close()
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

def _normalize_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    # Keep only digits for a canonical phone representation
    digits = ''.join(ch for ch in value if ch.isdigit())
    return digits or value.strip()


class ChatIn(BaseModel):
    text: str
    sender_id: Optional[str] = None  # keep stable per user/session
    phone_number: Optional[str] = None  # when provided, will be used to persist messages
    session_id: Optional[str] = None  # for token/session control
    new_session: Optional[bool] = False  # force creation of a new session id


class ChatOut(BaseModel):
    sender_id: str
    session_id: str
    replies: List[Dict[str, Any]]  # Rasa returns list of messages (text/image/buttons/...)

class ReleaseIn(BaseModel):
    session_id: str


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
    # Normalize phone for storage
    normalized_phone = _normalize_phone(payload.phone_number)
    # Session handling: if client requests new session or does not provide one, generate a new id.
    if payload.new_session or not (payload.session_id and payload.session_id.strip()):
        session_id = str(uuid.uuid4())
    else:
        session_id = payload.session_id.strip()
    # Greeting and request number on first contact (no phone number yet)
    if not payload.phone_number:
        greeting = "Hello I'm here to assist you for PAN and TAN and i'm comfortable in both the languages Hindi and English."
        ask_number = "Can you provide your number for the smooth conversation?"
        consent_note = "Please note: We need your consent to process your phone number for providing PAN/TAN assistance services."
        return {"sender_id": sender, "session_id": session_id, "replies": [{"text": greeting}, {"text": ask_number}, {"text": consent_note}]}

    # Handle OTP flow first when phone number provided; only talk to Rasa after verification
    # TEMP: Skip OTP flow; proceed directly with chat when phone provided.
    # Keeping original OTP code commented for future re-enable.
    if payload.phone_number and SessionLocal:
        db = SessionLocal()
        try:
            phone = normalized_phone or payload.phone_number.strip()
            # Ensure phone number stored in DB (without loading old history)
            try:
                ensure_phone_number(db, phone)
            except Exception:
                pass
            # If user just sent a phone number and no session_id was provided, start a brand-new session automatically
            normalized_text = _normalize_phone(payload.text) if payload.text else None
            looks_like_phone = bool(normalized_text and normalized_text.isdigit() and len(normalized_text) >= 10)
            if looks_like_phone and not (payload.session_id and payload.session_id.strip()):
                session_id = str(uuid.uuid4())
            # Acquire/verify session token before proceeding. If pool full, hold user.
            try:
                token_value, is_waiting = acquire_token(db, session_id)
            except Exception:
                token_value, is_waiting = 0, False
            if is_waiting:
                # Do not error; keep user waiting politely
                return {"sender_id": sender, "session_id": session_id, "replies": [{"text": "Please wait while we connect you..."}]}

            # ORIGINAL OTP FLOW (DISABLED):
            # If this is the first interaction after providing number, acknowledge and do not call Rasa yet
            try:
                existing_session = (
                    db.query(SessionChatHistory)
                    .filter(SessionChatHistory.session_id == session_id)
                    .first()
                )
            except Exception:
                existing_session = None
            
            # Check if this is the first message after phone number (no session history yet)
            is_first_message = existing_session is None or not (existing_session.history or '').strip()
            
            # Also check if user just sent their phone number (10+ digits)
            is_phone_number = payload.text and _normalize_phone(payload.text) and _normalize_phone(payload.text).isdigit() and len(_normalize_phone(payload.text)) >= 10
            
            if is_first_message or is_phone_number:
                try:
                    if payload.text:
                        append_session_history(db, session_id, f"user: {payload.text}", phone_number=phone)
                        append_number_history(db, phone, f"user: {payload.text}")
                    ack = f"Got your number: {phone}."
                    append_session_history(db, session_id, f"bot: {ack}", phone_number=phone)
                    append_number_history(db, phone, f"bot: {ack}")
                except Exception:
                    pass
                return {"sender_id": sender, "session_id": session_id, "replies": [{"text": ack}]}
            # if not is_phone_verified(db, phone):
            #     if payload.text and payload.text.strip().isdigit() and len(payload.text.strip()) == 6 and verify_otp and OTPVerifyRequest:
            #         resp = verify_otp(db, OTPVerifyRequest(phone_number=phone, otp_code=payload.text.strip()))
            #         if resp.success:
            #             return {"sender_id": sender, "replies": [{"text": "OTP verified. You can continue chatting now."}]}
            #         else:
            #             return {"sender_id": sender, "replies": [{"text": resp.message}]}
            #     if generate_otp and OTPGenerateRequest:
            #         _ = generate_otp(db, OTPGenerateRequest(phone_number=phone))
            #     return {"sender_id": sender, "replies": [{"text": "An OTP has been sent. Please enter the 6-digit code to proceed."}]}

            # If verified: proceed to send to Rasa below; we will persist after reply
        finally:
            db.close()

    # Only now talk to Rasa
    # Note: Removed special PAN/TAN handling to let Rasa manage the conversation flow properly
    # This ensures that context-aware processing happens through Rasa actions

    # Only now talk to Rasa
    data = {"sender": sender, "message": payload.text}
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(RASA_REST_URL, json=data)
            r.raise_for_status()
            replies = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Rasa unreachable: {e!s}")

    # Persist conversation for both session and number histories (OTP disabled)
    if payload.phone_number and SessionLocal:
        db = SessionLocal()
        try:
            phone = normalized_phone or payload.phone_number.strip()
            # Save user message into consolidated conversations table
            # This also triggers PAN extraction/storage when a PAN is present in the message
            try:
                save_conversation(
                    db,
                    ConversationCreate(
                        phone_number=phone, role="user", message=payload.text
                    ),
                )
            except Exception:
                pass
            try:
                append_session_history(db, session_id, f"user: {payload.text}", phone_number=phone)
                append_number_history(db, phone, f"user: {payload.text}")
            except Exception:
                pass
            for reply in replies:
                if isinstance(reply, dict) and reply.get("text"):
                    # Persist bot reply as well to maintain complete conversation context
                    try:
                        save_conversation(
                            db,
                            ConversationCreate(
                                phone_number=phone,
                                role="bot",
                                message=reply["text"],
                            ),
                        )
                    except Exception:
                        pass
                    try:
                        append_session_history(db, session_id, f"bot: {reply['text']}", phone_number=phone)
                        append_number_history(db, phone, f"bot: {reply['text']}")
                    except Exception:
                        pass
        finally:
            db.close()

    return {"sender_id": sender, "session_id": session_id, "replies": replies}


@app.post("/chat/release")
async def chat_release(payload: ReleaseIn):
    if not SessionLocal:
        return {"released": False}
    db = SessionLocal()
    try:
        sid = (payload.session_id or "").strip()
        if not sid:
            return {"released": False}
        try:
            release_token(db, sid)
            return {"released": True}
        except Exception:
            return {"released": False}
    finally:
        db.close()

