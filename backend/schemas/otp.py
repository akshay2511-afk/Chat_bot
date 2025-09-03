from datetime import datetime
from typing import Optional
from pydantic import BaseModel, constr, validator

PhoneNumberStr = constr(strip_whitespace=True, min_length=8, max_length=20)
OTPCodeStr = constr(strip_whitespace=True, min_length=6, max_length=6, regex=r'^\d{6}$')

class OTPGenerateRequest(BaseModel):
    phone_number: PhoneNumberStr

class OTPVerifyRequest(BaseModel):
    phone_number: PhoneNumberStr
    otp_code: OTPCodeStr

class OTPResponse(BaseModel):
    success: bool
    message: str
    phone_number: Optional[PhoneNumberStr] = None
    expires_at: Optional[datetime] = None

class OTPVerificationOut(BaseModel):
    id: int
    phone_number: PhoneNumberStr
    otp_code: str
    is_verified: bool
    attempts: int
    created_at: datetime
    expires_at: datetime
    verified_at: Optional[datetime]

    class Config:
        orm_mode = True
