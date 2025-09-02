from typing import List
from sqlalchemy.orm import Session
from backend.models.conversation import PhoneNumber, Conversation
from backend.schemas.conversation import ConversationCreate


def ensure_phone_number(db: Session, phone_number: str) -> PhoneNumber:
    entity = db.get(PhoneNumber, phone_number)
    if entity is None:
        entity = PhoneNumber(phone_number=phone_number)
        db.add(entity)
        db.commit()
        db.refresh(entity)
    return entity


def save_conversation(db: Session, payload: ConversationCreate) -> Conversation:
    ensure_phone_number(db, payload.phone_number)
    conv = Conversation(
        phone_number=payload.phone_number,
        role=payload.role,
        message=payload.message,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversations(db: Session, phone_number: str) -> List[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.phone_number == phone_number)
        .order_by(Conversation.created_at.asc())
        .all()
    )
