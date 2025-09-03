from sqlalchemy.orm import Session
from backend.models.history import NumberChatHistory, SessionChatHistory


def append_number_history(db: Session, phone_number: str, line: str) -> None:
    entity = db.get(NumberChatHistory, phone_number)
    if entity is None:
        entity = NumberChatHistory(phone_number=phone_number, history=line)
        db.add(entity)
    else:
        entity.history = f"{entity.history}\n{line}" if entity.history else line
    db.commit()


def append_session_history(db: Session, session_id: str, line: str, phone_number: str | None = None) -> None:
    row = db.query(SessionChatHistory).filter(SessionChatHistory.session_id == session_id).first()
    if row is None:
        row = SessionChatHistory(session_id=session_id, phone_number=phone_number, history=line)
        db.add(row)
    else:
        row.history = f"{row.history}\n{line}" if row.history else line
        if phone_number and not row.phone_number:
            row.phone_number = phone_number
    db.commit()


