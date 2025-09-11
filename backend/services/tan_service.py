from sqlalchemy.orm import Session
from backend.models.conversation import PhoneNumber
from backend.schemas.conversation import SaveTANRequest


def save_tan_number(db: Session, request: SaveTANRequest) -> bool:
    """Save TAN number for a phone number"""
    try:
        # Find existing phone number record
        phone_record = db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == request.phone_number
        ).first()
        
        if phone_record:
            # Update existing record with TAN number
            phone_record.tan_number = request.tan_number.upper()
            db.commit()
            return True
        else:
            # Create new phone number record with TAN
            new_record = PhoneNumber(
                phone_number=request.phone_number,
                tan_number=request.tan_number.upper()
            )
            db.add(new_record)
            db.commit()
            return True
    except Exception as e:
        db.rollback()
        print(f"Error saving TAN number: {e}")
        return False


def get_tan_number(db: Session, phone_number: str) -> str:
    """Get TAN number for a phone number"""
    try:
        phone_record = db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == phone_number
        ).first()
        
        if phone_record:
            return phone_record.tan_number
        return None
    except Exception as e:
        print(f"Error getting TAN number: {e}")
        return None
