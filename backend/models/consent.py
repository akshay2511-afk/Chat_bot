from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), ForeignKey("phone_numbers.phone_number"), nullable=False, index=True)
    consent_version = Column(String(10), nullable=False, default="1.0")  # Track consent policy versions
    purpose = Column(String(100), nullable=False)  # e.g., "PAN_TAN_ASSISTANCE", "DATA_ANALYTICS"
    granted = Column(Boolean, nullable=False, default=False)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 support
    user_agent = Column(Text, nullable=True)
    consent_text = Column(Text, nullable=False)  # Store exact consent text shown to user
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Audit trail
    created_by = Column(String(50), nullable=True)  # System identifier
    updated_by = Column(String(50), nullable=True)
    
    # Relationships
    phone_owner = relationship("PhoneNumber", back_populates="consents")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_consent_phone_purpose', 'phone_number', 'purpose'),
        Index('idx_consent_granted_at', 'granted_at'),
        Index('idx_consent_version', 'consent_version'),
    )

class ConsentPolicy(Base):
    __tablename__ = "consent_policies"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String(10), nullable=False, unique=True, index=True)
    purpose = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Full policy text
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(50), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_policy_purpose_active', 'purpose', 'is_active'),
        Index('idx_policy_effective', 'effective_from', 'effective_until'),
    )
