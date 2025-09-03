from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, Base, engine
from backend.schemas.otp import OTPGenerateRequest, OTPVerifyRequest, OTPResponse, OTPVerificationOut
from backend.services.otp_service import generate_otp, verify_otp, get_otp_status, is_phone_verified

# Ensure tables exist (simple bootstrap). In production use Alembic.
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/otp", tags=["otp"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate", response_model=OTPResponse)
def api_generate_otp(request: OTPGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate OTP for phone number verification.
    """
    result = generate_otp(db, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

@router.post("/verify", response_model=OTPResponse)
def api_verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP for phone number.
    """
    result = verify_otp(db, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

@router.get("/status/{phone_number}", response_model=OTPVerificationOut)
def api_get_otp_status(phone_number: str, db: Session = Depends(get_db)):
    """
    Get OTP verification status for a phone number.
    """
    otp_status = get_otp_status(db, phone_number)
    if not otp_status:
        raise HTTPException(status_code=404, detail="No OTP found for this phone number")
    return OTPVerificationOut.from_orm(otp_status)

@router.get("/verified/{phone_number}")
def api_check_phone_verified(phone_number: str, db: Session = Depends(get_db)):
    """
    Check if a phone number has been verified with OTP.
    """
    verified = is_phone_verified(db, phone_number)
    return {"phone_number": phone_number, "verified": verified}
