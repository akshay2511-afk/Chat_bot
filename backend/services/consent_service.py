from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.models.consent import Consent, ConsentPolicy
from backend.models.conversation import PhoneNumber
from backend.schemas.consent import (
    ConsentCreate, ConsentPurpose, ConsentStatus, 
    ConsentCheckResponse, ConsentPolicyResponse, ConsentBannerData
)

def get_active_policy(db: Session, purpose: ConsentPurpose) -> Optional[ConsentPolicy]:
    """Get the currently active consent policy for a given purpose."""
    now = datetime.utcnow()
    return (
        db.query(ConsentPolicy)
        .filter(
            ConsentPolicy.purpose == purpose.value,
            ConsentPolicy.is_active == True,
            ConsentPolicy.effective_from <= now,
            or_(
                ConsentPolicy.effective_until.is_(None),
                ConsentPolicy.effective_until > now
            )
        )
        .order_by(ConsentPolicy.effective_from.desc())
        .first()
    )

def check_consent(db: Session, phone_number: str, purpose: ConsentPurpose) -> ConsentCheckResponse:
    """Check if user has valid consent for the given purpose."""
    # Get active policy
    policy = get_active_policy(db, purpose)
    if not policy:
        return ConsentCheckResponse(
            has_consent=False,
            consent_status=None,
            consent_version=None,
            granted_at=None,
            requires_new_consent=True,
            current_policy=None
        )
    
    # Check for existing consent
    existing_consent = (
        db.query(Consent)
        .filter(
            Consent.phone_number == phone_number,
            Consent.purpose == purpose.value,
            Consent.granted == True,
            Consent.revoked_at.is_(None)
        )
        .order_by(Consent.created_at.desc())
        .first()
    )
    
    if not existing_consent:
        return ConsentCheckResponse(
            has_consent=False,
            consent_status=ConsentStatus.PENDING,
            consent_version=None,
            granted_at=None,
            requires_new_consent=True,
            current_policy=ConsentPolicyResponse.from_orm(policy)
        )
    
    # Check if consent is for current policy version
    requires_new_consent = existing_consent.consent_version != policy.version
    
    return ConsentCheckResponse(
        has_consent=not requires_new_consent,
        consent_status=ConsentStatus.GRANTED if not requires_new_consent else ConsentStatus.PENDING,
        consent_version=existing_consent.consent_version,
        granted_at=existing_consent.granted_at,
        requires_new_consent=requires_new_consent,
        current_policy=ConsentPolicyResponse.from_orm(policy)
    )

def create_consent(db: Session, consent_data: ConsentCreate) -> Consent:
    """Create a new consent record."""
    # Ensure phone number exists
    phone = db.get(PhoneNumber, consent_data.phone_number)
    if not phone:
        phone = PhoneNumber(phone_number=consent_data.phone_number)
        db.add(phone)
        db.flush()
    
    # Get current policy version
    policy = get_active_policy(db, ConsentPurpose(consent_data.purpose))
    if not policy:
        raise ValueError(f"No active policy found for purpose: {consent_data.purpose}")
    
    # Revoke any existing consent for this purpose
    existing_consents = (
        db.query(Consent)
        .filter(
            Consent.phone_number == consent_data.phone_number,
            Consent.purpose == consent_data.purpose.value,
            Consent.revoked_at.is_(None)
        )
        .all()
    )
    
    for existing in existing_consents:
        existing.revoked_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        existing.updated_by = "system"
    
    # Create new consent
    consent = Consent(
        phone_number=consent_data.phone_number,
        consent_version=policy.version,
        purpose=consent_data.purpose.value,
        granted=consent_data.granted,
        granted_at=datetime.utcnow() if consent_data.granted else None,
        ip_address=consent_data.ip_address,
        user_agent=consent_data.user_agent,
        consent_text=consent_data.consent_text,
        created_by="system",
        updated_by="system"
    )
    
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent

def get_consent_banner_data(db: Session, phone_number: str, purpose: ConsentPurpose) -> ConsentBannerData:
    """Get data needed for consent banner display."""
    policy = get_active_policy(db, purpose)
    if not policy:
        raise ValueError(f"No active policy found for purpose: {purpose}")
    
    # Check existing consent
    consent_check = check_consent(db, phone_number, purpose)
    
    return ConsentBannerData(
        policy=ConsentPolicyResponse.from_orm(policy),
        has_existing_consent=consent_check.has_consent,
        existing_consent_version=consent_check.consent_version,
        requires_consent=consent_check.requires_new_consent
    )

def revoke_consent(db: Session, phone_number: str, purpose: ConsentPurpose, reason: Optional[str] = None) -> bool:
    """Revoke existing consent for a phone number and purpose."""
    consents = (
        db.query(Consent)
        .filter(
            Consent.phone_number == phone_number,
            Consent.purpose == purpose.value,
            Consent.granted == True,
            Consent.revoked_at.is_(None)
        )
        .all()
    )
    
    if not consents:
        return False
    
    now = datetime.utcnow()
    for consent in consents:
        consent.revoked_at = now
        consent.updated_at = now
        consent.updated_by = "system"
    
    db.commit()
    return True

def get_consent_history(db: Session, phone_number: str, purpose: Optional[ConsentPurpose] = None) -> List[Consent]:
    """Get consent history for a phone number."""
    query = db.query(Consent).filter(Consent.phone_number == phone_number)
    
    if purpose:
        query = query.filter(Consent.purpose == purpose.value)
    
    return query.order_by(Consent.created_at.desc()).all()

def seed_default_policies(db: Session) -> None:
    """Seed default consent policies for the system."""
    policies = [
        {
            "version": "1.0",
            "purpose": ConsentPurpose.PAN_TAN_ASSISTANCE.value,
            "title": "PAN/TAN Assistance Consent",
            "content": """By providing your phone number, you consent to:

1. Collection and processing of your phone number for PAN/TAN assistance services
2. Storage of conversation history for service improvement
3. Use of your data for providing tax-related assistance
4. Contact for follow-up services if required

Your data will be retained for 7 years as per tax regulations and will be used solely for providing PAN/TAN assistance services.

You can revoke this consent at any time by contacting our support team.""",
            "effective_from": datetime.utcnow(),
            "created_by": "system"
        }
    ]
    
    for policy_data in policies:
        existing = db.query(ConsentPolicy).filter(
            ConsentPolicy.version == policy_data["version"],
            ConsentPolicy.purpose == policy_data["purpose"]
        ).first()
        
        if not existing:
            policy = ConsentPolicy(**policy_data)
            db.add(policy)
    
    db.commit()
