from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session
from backend.models.history import SessionToken


MAX_TOKENS = 10


def initialize_token_pool(db: Session) -> None:
    existing = db.query(SessionToken).count()
    if existing >= MAX_TOKENS:
        return
    present = {row.token for row in db.query(SessionToken).all()}
    for t in range(1, MAX_TOKENS + 1):
        if t not in present:
            db.add(SessionToken(token=t, is_busy=False))
    db.commit()


def acquire_token(db: Session, session_id: str) -> Tuple[int, bool]:
    """
    Try to acquire a free token for the given session_id.
    Returns (token_number, is_waiting)
    - If all tokens busy, returns (0, True) meaning on hold.
    - If session already had a token, returns that token.
    """
    initialize_token_pool(db)
    # If session already assigned, reuse
    existing = (
        db.query(SessionToken)
        .filter(SessionToken.session_id == session_id, SessionToken.is_busy == True)
        .first()
    )
    if existing:
        return existing.token, False

    free_row = (
        db.query(SessionToken)
        .filter(SessionToken.is_busy == False)
        .order_by(SessionToken.token.asc())
        .first()
    )
    if not free_row:
        return 0, True

    free_row.is_busy = True
    free_row.session_id = session_id
    free_row.assigned_at = datetime.utcnow()
    db.commit()
    db.refresh(free_row)
    return free_row.token, False


def release_token(db: Session, session_id: str) -> None:
    row = (
        db.query(SessionToken)
        .filter(SessionToken.session_id == session_id, SessionToken.is_busy == True)
        .first()
    )
    if row:
        row.is_busy = False
        row.session_id = None
        row.assigned_at = None
        db.commit()

