from fastapi import APIRouter
from pydantic import BaseModel, constr


class TANStatusRequest(BaseModel):
    tan_number: constr(strip_whitespace=True, min_length=10, max_length=10)


class TANStatusResponse(BaseModel):
    tan_number: str
    status: str
    message: str


router = APIRouter(prefix="/tan", tags=["tan"]) 


@router.post("/status", response_model=TANStatusResponse)
def get_tan_status(payload: TANStatusRequest) -> TANStatusResponse:
    tan = (payload.tan_number or "").strip().upper()
    # Static response for now as requested
    return TANStatusResponse(
        tan_number=tan,
        status="in_progress",
        message="Your TAN application is in progress. Please check back later.",
    )
