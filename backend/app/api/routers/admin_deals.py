from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin_access
from app.db.models.deal import Deal
from app.schemas.deal import (
    AdminDealCreateFromOfferRequest,
    AdminDealCreateRequest,
    AdminDealResponse,
)
from app.services.deal_service import DealService

router = APIRouter(
    prefix="/admin/deals",
    tags=["admin deals"],
    dependencies=[Depends(require_admin_access)],
)


@router.get("", response_model=list[AdminDealResponse])
def get_deals(
    db: Session = Depends(get_db),
    is_public: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Deal).order_by(Deal.step_number.asc())

    if is_public is not None:
        query = query.where(Deal.is_public == is_public)

    return db.scalars(query.limit(limit).offset(offset)).all()

@router.post("", response_model=AdminDealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(
    request: AdminDealCreateRequest,
    db: Session = Depends(get_db),
):
    service = DealService(db)

    try:
        return service.create_deal(request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/from-offer/{offer_id}",
    response_model=AdminDealResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deal_from_offer(
    offer_id: UUID,
    request: AdminDealCreateFromOfferRequest,
    db: Session = Depends(get_db),
):
    service = DealService(db)

    try:
        return service.create_deal_from_offer(offer_id, request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


