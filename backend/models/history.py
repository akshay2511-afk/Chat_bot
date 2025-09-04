from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.orm import validates, relationship
from backend.db.session import Base


class NumberChatHistory(Base):
    __tablename__ = "number_chathistory"

    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), primary_key=True, index=True)
    history = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Link to phone_numbers
    phone_owner = relationship("PhoneNumber", backref="number_chat_history", uselist=False)

    @validates("phone_number")
    def validate_phone(self, key, value):
        return (value or "").strip()


class SessionChatHistory(Base):
    __tablename__ = "session_chathistory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), index=True, nullable=True)
    history = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Link back to phone_numbers
    phone_owner = relationship("PhoneNumber", backref="session_chat_histories")

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_session_chat_history_session"),
    )


class SessionToken(Base):
    __tablename__ = "session_token"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(Integer, nullable=False, unique=True, index=True)  # 1..10
    is_busy = Column(Boolean, default=False, nullable=False)
    session_id = Column(String(64), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)


class Complaint(Base):
    __tablename__ = "complaint"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), index=True, nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to phone number
    phone_owner = relationship("PhoneNumber", backref="complaints")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), index=True, nullable=True)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to phone number
    phone_owner = relationship("PhoneNumber", backref="feedbacks")


class Suggestion(Base):
    __tablename__ = "suggestion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), index=True, nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to phone number
    phone_owner = relationship("PhoneNumber", backref="suggestions")


