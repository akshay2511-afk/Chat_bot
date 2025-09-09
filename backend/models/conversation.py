from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.session import Base

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    phone_number = Column(String(20), primary_key=True, index=True)
    pan_number = Column(String(10), nullable=True, index=True)
    tan_number = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="phone_owner", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    owner = relationship("PhoneNumber", back_populates="conversations")
