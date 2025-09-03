from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
from backend.models.history import Complaint, Feedback, Suggestion


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/complaint")
def submit_complaint(message: str, phone_number: str | None = None, db: Session = Depends(get_db)):
    row = Complaint(message=message, phone_number=(phone_number or "").strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.post("/feedback")
def submit_feedback(message: str, rating: int | None = None, phone_number: str | None = None, db: Session = Depends(get_db)):
    row = Feedback(message=message, rating=rating, phone_number=(phone_number or "").strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.post("/suggestion")
def submit_suggestion(message: str, phone_number: str | None = None, db: Session = Depends(get_db)):
    row = Suggestion(message=message, phone_number=(phone_number or "").strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


