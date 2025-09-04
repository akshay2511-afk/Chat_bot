from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from backend.models.history import SessionToken
from backend.models.history import SessionChatHistory


MAX_TOKENS = 10
TOKEN_TTL_MINUTES = 15  # consider a session inactive after 15 minutes of no updates


def initialize_token_pool(db: Session) -> None:
    existing = db.query(SessionToken).count()
    if existing >= MAX_TOKENS:
        return
    present = {row.token for row in db.query(SessionToken).all()}
    for t in range(1, MAX_TOKENS + 1):
        if t not in present:
            db.add(SessionToken(token=t, is_busy=False))
    db.commit()


def _release_stale_tokens(db: Session) -> None:
    """Free tokens whose sessions have gone inactive or are invalid."""
    cutoff = datetime.utcnow() - timedelta(minutes=TOKEN_TTL_MINUTES)
    busy_tokens = db.query(SessionToken).filter(SessionToken.is_busy == True).all()
    for tok in busy_tokens:
        should_release = False
        # No session id or assigned long ago
        if not tok.session_id:
            should_release = True
        elif tok.assigned_at and tok.assigned_at < cutoff:
            should_release = True
        else:
            # If there is no chat history for this session_id or it's stale, release
            hist = (
                db.query(SessionChatHistory)
                .filter(SessionChatHistory.session_id == tok.session_id)
                .first()
            )
            if hist is None:
                should_release = True
            else:
                # If no updates in a while, consider session closed
                if (hist.updated_at or hist.created_at) < cutoff:
                    should_release = True
        if should_release:
            tok.is_busy = False
            tok.session_id = None
            tok.assigned_at = None
    db.commit()


def acquire_token(db: Session, session_id: str) -> Tuple[int, bool]:
    """
    Try to acquire a free token for the given session_id.
    Returns (token_number, is_waiting)
    - If all tokens busy, returns (0, True) meaning on hold.
    - If session already had a token, returns that token.
    """
    initialize_token_pool(db)
    # Proactively free tokens from stale/closed sessions
    _release_stale_tokens(db)

    # (Reverted) Do not block other sessions globally; allow multiple tokens.
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

