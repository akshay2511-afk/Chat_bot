from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.otp import OTPVerification
from backend.models.conversation import PhoneNumber
from backend.schemas.otp import OTPGenerateRequest, OTPVerifyRequest, OTPResponse
from backend.services.conversation_service import ensure_phone_number

# Static OTP for now as requested
STATIC_OTP = "000000"
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3

def generate_otp(db: Session, request: OTPGenerateRequest) -> OTPResponse:
    """
    Generate OTP for phone number verification.
    For now, uses static OTP '000000' as requested.
    """
    try:
        # Ensure phone number exists
        ensure_phone_number(db, request.phone_number)
        
        # Check if there's an existing unverified OTP
        existing_otp = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.phone_number == request.phone_number,
                OTPVerification.is_verified == False,
                OTPVerification.expires_at > datetime.utcnow()
            )
            .first()
        )
        
        if existing_otp:
            return OTPResponse(
                success=True,
                message="OTP already sent. Please check your messages or wait for expiry.",
                phone_number=request.phone_number,
                expires_at=existing_otp.expires_at
            )
        
        # Create new OTP verification record
        expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        otp_record = OTPVerification(
            phone_number=request.phone_number,
            otp_code=STATIC_OTP,
            expires_at=expires_at
        )
        
        db.add(otp_record)
        db.commit()
        db.refresh(otp_record)
        
        return OTPResponse(
            success=True,
            message=f"OTP sent successfully. Please enter the 6-digit code. (For testing: {STATIC_OTP})",
            phone_number=request.phone_number,
            expires_at=expires_at
        )
        
    except Exception as e:
        db.rollback()
        return OTPResponse(
            success=False,
            message=f"Failed to generate OTP: {str(e)}"
        )

def verify_otp(db: Session, request: OTPVerifyRequest) -> OTPResponse:
    """
    Verify OTP for phone number.
    """
    try:
        # Find the most recent unverified OTP for this phone number
        otp_record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.phone_number == request.phone_number,
                OTPVerification.is_verified == False
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )
        
        if not otp_record:
            return OTPResponse(
                success=False,
                message="No OTP found for this phone number. Please request a new OTP."
            )
        
        # Check if OTP has expired
        if datetime.utcnow() > otp_record.expires_at:
            return OTPResponse(
                success=False,
                message="OTP has expired. Please request a new OTP."
            )
        
        # Check if max attempts exceeded
        if otp_record.attempts >= MAX_ATTEMPTS:
            return OTPResponse(
                success=False,
                message="Maximum verification attempts exceeded. Please request a new OTP."
            )
        
        # Increment attempts
        otp_record.attempts += 1
        
        # Verify OTP
        if otp_record.otp_code == request.otp_code:
            otp_record.is_verified = True
            otp_record.verified_at = datetime.utcnow()
            db.commit()
            
            return OTPResponse(
                success=True,
                message="OTP verified successfully! You can now access your chat history.",
                phone_number=request.phone_number
            )
        else:
            db.commit()
            remaining_attempts = MAX_ATTEMPTS - otp_record.attempts
            
            if remaining_attempts > 0:
                return OTPResponse(
                    success=False,
                    message=f"Invalid OTP. {remaining_attempts} attempts remaining."
                )
            else:
                return OTPResponse(
                    success=False,
                    message="Maximum verification attempts exceeded. Please request a new OTP."
                )
                
    except Exception as e:
        db.rollback()
        return OTPResponse(
            success=False,
            message=f"Failed to verify OTP: {str(e)}"
        )

def get_otp_status(db: Session, phone_number: str) -> Optional[OTPVerification]:
    """
    Get the current OTP verification status for a phone number.
    """
    return (
        db.query(OTPVerification)
        .filter(OTPVerification.phone_number == phone_number)
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

def is_phone_verified(db: Session, phone_number: str) -> bool:
    """
    Check if the MOST RECENT OTP for this phone number is verified and not expired.
    This enforces OTP per-session: older verifications are ignored.
    """
    latest = (
        db.query(OTPVerification)
        .filter(OTPVerification.phone_number == phone_number)
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    if latest is None:
        return False
    if latest.expires_at and datetime.utcnow() > latest.expires_at:
        return False
    return bool(latest.is_verified)
