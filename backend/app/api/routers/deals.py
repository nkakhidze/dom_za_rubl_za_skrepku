from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.deal import DealCreateRequest, DealCreateResponse
from app.services.deal_service import DealService


router = APIRouter(
    prefix="/deals",
    tags=["deals"],
)


@router.post("", response_model=DealCreateResponse, status_code=status.HTTP_201_CREATED)
def create_deal(
    request: DealCreateRequest,
    db: Session = Depends(get_db),
):
    service = DealService(db)

    try:
        return service.create_response_deal(request)
    except ValueError as error:
        message = str(error)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error
