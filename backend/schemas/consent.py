from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, constr, validator
from enum import Enum

PhoneNumberStr = constr(strip_whitespace=True, min_length=8, max_length=20)

class ConsentPurpose(str, Enum):
    PAN_TAN_ASSISTANCE = "PAN_TAN_ASSISTANCE"
    DATA_ANALYTICS = "DATA_ANALYTICS"
    MARKETING = "MARKETING"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"

class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    PENDING = "PENDING"

class ConsentCreate(BaseModel):
    phone_number: PhoneNumberStr
    purpose: ConsentPurpose
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    consent_text: str
    
    @validator('consent_text')
    def validate_consent_text(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Consent text must be at least 10 characters')
        return v.strip()

class ConsentResponse(BaseModel):
    id: int
    phone_number: PhoneNumberStr
    consent_version: str
    purpose: str
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    consent_text: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ConsentPolicyResponse(BaseModel):
    id: int
    version: str
    purpose: str
    title: str
    content: str
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime]
    
    class Config:
        orm_mode = True

class ConsentCheckRequest(BaseModel):
    phone_number: PhoneNumberStr
    purpose: ConsentPurpose

class ConsentCheckResponse(BaseModel):
    has_consent: bool
    consent_status: Optional[ConsentStatus]
    consent_version: Optional[str]
    granted_at: Optional[datetime]
    requires_new_consent: bool
    current_policy: Optional[ConsentPolicyResponse]

class ConsentRevokeRequest(BaseModel):
    phone_number: PhoneNumberStr
    purpose: ConsentPurpose
    reason: Optional[str] = None

class ConsentBannerData(BaseModel):
    policy: ConsentPolicyResponse
    has_existing_consent: bool
    existing_consent_version: Optional[str]
    requires_consent: bool
