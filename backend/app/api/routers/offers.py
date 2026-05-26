from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.db.models.offer import Offer
from app.schemas.offer import (
    OfferCreateRequest,
    OfferCreateResponse,
    OfferLimitResponse,
    PublicOfferDetail,
    PublicOfferListItem,
)
from app.services.offer_limit_service import OfferLimitResult
from app.services.offer_service import OfferService

router = APIRouter(
    prefix="/offers",
    tags=["offers"],
)


@router.get("", response_model=list[PublicOfferListItem])
def get_public_offers(
    db: Session = Depends(get_db),
):
    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(Offer.is_public.is_(True))
        .order_by(Offer.created_at.desc())
    )

    return db.scalars(query).all()


@router.get("/{offer_id}", response_model=PublicOfferDetail)
def get_public_offer(
    offer_id: UUID,
    db: Session = Depends(get_db),
):
    offer = db.scalar(
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(
            Offer.id == offer_id,
            Offer.is_public.is_(True),
        )
    )

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found",
        )

    return offer


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
