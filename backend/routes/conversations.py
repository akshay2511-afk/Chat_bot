from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
from backend.schemas.conversation import ConversationCreate, ConversationOut, ConversationList
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


@router.get("/{phone_number}", response_model=ConversationList)
def api_get_conversations(phone_number: str, db: Session = Depends(get_db)):
    rows = get_conversations(db, phone_number)
    serialized: List[ConversationOut] = [ConversationOut.from_orm(r) for r in rows]
    return ConversationList(phone_number=phone_number, conversations=serialized)
