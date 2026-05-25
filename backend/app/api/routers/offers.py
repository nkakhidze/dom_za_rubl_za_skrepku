from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.offer import Offer
from app.schemas.offer import OfferCreateRequest, OfferCreateResponse, OfferLimitResponse
from app.services.offer_limit_service import OfferLimitResult
from app.services.offer_service import OfferService

router = APIRouter(
    prefix="/offers",
    tags=["offers"],
)


@router.post(
    "",
    response_model=OfferCreateResponse | OfferLimitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_offer(
    request: OfferCreateRequest,
    db: Session = Depends(get_db),
):
    service = OfferService(db)

    try:
        result = service.create_offer(request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if isinstance(result, OfferLimitResult):
        return OfferLimitResponse(
            next_allowed_date=result.next_allowed_date,
            message=result.message,
        )

    if isinstance(result, Offer):
        return OfferCreateResponse(
            id=result.id,
            status=result.status,
            message="Предложение успешно отправлено на модерацию",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Неожиданный результат создания предложения",
    )