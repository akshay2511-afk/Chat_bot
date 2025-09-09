from fastapi import APIRouter
from pydantic import BaseModel, constr


class PANStatusRequest(BaseModel):
    pan_number: constr(strip_whitespace=True, min_length=10, max_length=10)


class PANStatusResponse(BaseModel):
    pan_number: str
    status: str
    message: str


router = APIRouter(prefix="/pan", tags=["pan"]) 


@router.post("/status", response_model=PANStatusResponse)
def get_pan_status(payload: PANStatusRequest) -> PANStatusResponse:
    pan = (payload.pan_number or "").strip().upper()
    # Static response for now as requested
    return PANStatusResponse(
        pan_number=pan,
        status="in_progress",
        message="Your PAN application is in progress. Please check back later.",
    )

