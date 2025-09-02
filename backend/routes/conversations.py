from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
from backend.schemas.conversation import ConversationCreate, ConversationOut, ConversationSingle
from backend.services.conversation_service import save_conversation, get_conversations

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
