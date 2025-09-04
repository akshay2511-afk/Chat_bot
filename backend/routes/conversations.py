from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
# Ensure all models are registered before creating tables
from backend.models import history as _history_models  # noqa: F401
from backend.schemas.conversation import ConversationCreate, ConversationOut, ConversationSingle
from backend.services.conversation_service import save_conversation, get_conversations, ensure_phone_number

# Ensure tables exist (simple bootstrap). In production use Alembic.
Base.metadata.create_all(bind=engine)

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
