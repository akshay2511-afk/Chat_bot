from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.session import Base

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)  # 6-digit OTP
    is_verified = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)  # Track failed attempts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # OTP expires after 5 minutes
    verified_at = Column(DateTime, nullable=True)  # When OTP was successfully verified

    # Relationship to phone number
    phone_owner = relationship("PhoneNumber", backref="otp_verifications")
