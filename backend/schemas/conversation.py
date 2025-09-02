from datetime import datetime
from typing import Optional
from pydantic import BaseModel, constr

PhoneNumberStr = constr(strip_whitespace=True, min_length=8, max_length=20)

class ConversationCreate(BaseModel):
    phone_number: PhoneNumberStr
    role: str  # 'user' or 'bot'
    message: str

class ConversationOut(BaseModel):
    id: int
    phone_number: PhoneNumberStr
    role: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True

class ConversationSingle(BaseModel):
    phone_number: PhoneNumberStr
    conversation: Optional[ConversationOut]
