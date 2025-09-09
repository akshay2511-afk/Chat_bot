from typing import List, Optional
import re
from sqlalchemy.orm import Session
from backend.models.conversation import PhoneNumber, Conversation
from backend.models.history import NumberChatHistory, SessionChatHistory
from backend.schemas.conversation import ConversationCreate


def ensure_phone_number(db: Session, phone_number: str) -> PhoneNumber:
    entity = db.get(PhoneNumber, phone_number)
    if entity is None:
        entity = PhoneNumber(phone_number=phone_number)
        db.add(entity)
        db.commit()
        db.refresh(entity)
    return entity


def save_pan_number(db: Session, phone_number: str, pan_number: str) -> PhoneNumber:
    """Upsert PAN number for a given phone number.

    - Normalizes case to uppercase
    - Overwrites previously saved value when new valid PAN is provided
    """
    entity = ensure_phone_number(db, phone_number)
    normalized_pan = (pan_number or "").strip().upper()
    entity.pan_number = normalized_pan or None
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def save_tan_number(db: Session, phone_number: str, tan_number: str) -> PhoneNumber:
    """Upsert TAN number for a given phone number.

    - Normalizes case to uppercase
    - Overwrites previously saved value when new valid TAN is provided
    """
    entity = ensure_phone_number(db, phone_number)
    normalized_tan = (tan_number or "").strip().upper()
    entity.tan_number = normalized_tan or None
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

    # If user message contains a PAN/TAN, persist it on the phone_numbers row
    try:
        if payload.role.lower() == "user":
            message_text = (payload.message or "").strip().upper()
            pan_match = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", message_text)
            if pan_match:
                save_pan_number(db, payload.phone_number, pan_match.group(0))
            tan_match = re.search(r"\b[A-Z]{4}\d{5}[A-Z]\b", message_text)
            if tan_match:
                save_tan_number(db, payload.phone_number, tan_match.group(0))
    except Exception:
        # Do not block conversation saving if PAN save fails
        pass

    db.commit()
    db.refresh(conv)

    # Mirror conversation into new history tables
    # - number_chathistory: append full formatted line
    # - session_chathistory: append if a session_id is provided in message header (optional convention)
    formatted_line = formatted
    nch: NumberChatHistory | None = db.get(NumberChatHistory, payload.phone_number)
    if nch is None:
        nch = NumberChatHistory(phone_number=payload.phone_number, history=formatted_line)
        db.add(nch)
    else:
        nch.history = f"{nch.history}\n{formatted_line}" if nch.history else formatted_line

    # Best-effort commit for histories (won't break original flow if fails)
    try:
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.refresh(nch)
    except Exception:
        pass
    return conv


def get_conversations(db: Session, phone_number: str) -> Optional[Conversation]:
    """Return the single conversation row for a phone number, if any."""
    return (
        db.query(Conversation)
        .filter(Conversation.phone_number == phone_number)
        .order_by(Conversation.id.asc())
        .first()
    )
