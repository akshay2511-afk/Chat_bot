from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
# Ensure all models are registered before creating tables
from backend.models import history as _history_models  # noqa: F401
from backend.schemas.conversation import ConversationCreate, ConversationOut, ConversationSingle, SavePANRequest, SaveTANRequest
from backend.services.conversation_service import save_conversation, get_conversations, ensure_phone_number, save_pan_number, save_tan_number

# Ensure tables exist (simple bootstrap). In production use Alembic.
Base.metadata.create_all(bind=engine)

# Lightweight migration: add pan_number and tan_number columns if missing
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE phone_numbers ADD COLUMN IF NOT EXISTS pan_number VARCHAR(10);"))
        conn.execute(text("ALTER TABLE phone_numbers ADD COLUMN IF NOT EXISTS tan_number VARCHAR(10);"))
except Exception:
    # Non-fatal: do not crash API startup if migration step fails
    pass

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ConversationOut)
def api_save_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    conv = save_conversation(db, payload)
    return ConversationOut.from_orm(conv)


@router.get("/{phone_number}", response_model=ConversationSingle)
def api_get_conversations(phone_number: str, db: Session = Depends(get_db)):
    row = get_conversations(db, phone_number)
    serialized = ConversationOut.from_orm(row) if row else None
    return ConversationSingle(phone_number=phone_number, conversation=serialized)


@router.post("/ensure/{phone_number}")
def api_ensure_phone(phone_number: str, db: Session = Depends(get_db)):
    try:
        entity = ensure_phone_number(db, phone_number)
        return {"phone_number": entity.phone_number, "created": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pan")
def api_save_pan(payload: SavePANRequest, db: Session = Depends(get_db)):
    try:
        entity = save_pan_number(db, payload.phone_number, payload.pan_number)
        return {"phone_number": entity.phone_number, "pan_number": entity.pan_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tan")
def api_save_tan(payload: SaveTANRequest, db: Session = Depends(get_db)):
    try:
        entity = save_tan_number(db, payload.phone_number, payload.tan_number)
        return {"phone_number": entity.phone_number, "tan_number": entity.tan_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
