from typing import List, Optional
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
    """
    Upsert conversation history for a phone number.
    - Ensures a PhoneNumber entity exists
    - Keeps a single Conversation row per phone_number
    - Appends new messages to the existing message field with role prefix
    """
    ensure_phone_number(db, payload.phone_number)

    # Try to get existing conversation entry for this phone number
    conv: Conversation | None = (
        db.query(Conversation)
        .filter(Conversation.phone_number == payload.phone_number)
        .order_by(Conversation.id.asc())
        .first()
    )

    formatted = f"{payload.role}: {payload.message}".strip()

    if conv is None:
        # Create a single row and store the first message
        conv = Conversation(
            phone_number=payload.phone_number,
            role=payload.role,
            message=formatted,
        )
        db.add(conv)
    else:
        # Append to existing history and update role to last speaker
        if conv.message:
            conv.message = f"{conv.message}\n{formatted}"
        else:
            conv.message = formatted
        conv.role = payload.role

        # If there are stray additional rows for this phone number, delete them
        extras: List[Conversation] = (
            db.query(Conversation)
            .filter(Conversation.phone_number == payload.phone_number, Conversation.id != conv.id)
            .all()
        )
        for extra in extras:
            db.delete(extra)

    db.commit()
    db.refresh(conv)
    return conv


def get_conversations(db: Session, phone_number: str) -> Optional[Conversation]:
    """Return the single conversation row for a phone number, if any."""
    return (
        db.query(Conversation)
        .filter(Conversation.phone_number == phone_number)
        .order_by(Conversation.id.asc())
        .first()
    )
