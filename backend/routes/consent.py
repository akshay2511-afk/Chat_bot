from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from backend.db.session import SessionLocal
from backend.schemas.consent import (
    ConsentCreate, ConsentResponse, ConsentCheckRequest, ConsentCheckResponse,
    ConsentRevokeRequest, ConsentBannerData, ConsentPurpose
)
from backend.services.consent_service import (
    create_consent, check_consent, get_consent_banner_data, 
    revoke_consent, get_consent_history, seed_default_policies
)

router = APIRouter(prefix="/consent", tags=["consent"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/check", response_model=ConsentCheckResponse)
def check_user_consent(
    request: ConsentCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if user has valid consent for a specific purpose."""
    try:
        return check_consent(db, request.phone_number, request.purpose)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check consent: {str(e)}")

@router.post("/banner-data", response_model=ConsentBannerData)
def get_banner_data(
    request: ConsentCheckRequest,
    db: Session = Depends(get_db)
):
    """Get consent banner data for UI display."""
    try:
        return get_consent_banner_data(db, request.phone_number, request.purpose)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get banner data: {str(e)}")

@router.post("/grant", response_model=ConsentResponse)
def grant_consent(
    request: ConsentCreate,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Grant consent for data processing."""
    try:
        # Add request metadata
        request.ip_address = get_client_ip(http_request)
        request.user_agent = http_request.headers.get("User-Agent", "unknown")
        
        consent = create_consent(db, request)
        return ConsentResponse.from_orm(consent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grant consent: {str(e)}")

@router.post("/revoke")
def revoke_user_consent(
    request: ConsentRevokeRequest,
    db: Session = Depends(get_db)
):
    """Revoke existing consent."""
    try:
        success = revoke_consent(db, request.phone_number, request.purpose, request.reason)
        if not success:
            raise HTTPException(status_code=404, detail="No active consent found to revoke")
        return {"message": "Consent revoked successfully", "revoked": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke consent: {str(e)}")

@router.get("/history/{phone_number}", response_model=List[ConsentResponse])
def get_user_consent_history(
    phone_number: str,
    purpose: ConsentPurpose = None,
    db: Session = Depends(get_db)
):
    """Get consent history for a phone number."""
    try:
        history = get_consent_history(db, phone_number, purpose)
        return [ConsentResponse.from_orm(consent) for consent in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consent history: {str(e)}")

@router.post("/seed-policies")
def seed_policies(db: Session = Depends(get_db)):
    """Seed default consent policies (admin endpoint)."""
    try:
        seed_default_policies(db)
        return {"message": "Default policies seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed policies: {str(e)}")
