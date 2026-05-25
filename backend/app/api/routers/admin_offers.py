from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.offer import Offer
from app.schemas.offer import (
    AdminOfferDetail,
    AdminOfferListItem,
    AdminOfferModerationUpdateRequest,
    AdminOfferStatusUpdateRequest,
)

router = APIRouter(
    prefix="/admin/offers",
    tags=["admin offers"],
)


@router.get("", response_model=list[AdminOfferListItem])
def get_offers(
    db: Session = Depends(get_db),
    offer_status: str | None = Query(default=None, description="Фильтр по статусу заявки"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Offer).order_by(Offer.created_at.desc())

    if offer_status is not None:
        query = query.where(Offer.status == offer_status)

    offers = db.scalars(
        query.limit(limit).offset(offset)
    ).all()

    return offers


@router.get("/{offer_id}", response_model=AdminOfferDetail)
def get_offer(
    offer_id: UUID,
    db: Session = Depends(get_db),
):
    offer = db.get(Offer, offer_id)

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    return offer


@router.patch("/{offer_id}/status", response_model=AdminOfferDetail)
def update_offer_status(
    offer_id: UUID,
    request: AdminOfferStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    offer = db.get(Offer, offer_id)

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    offer.status = request.status.value

    db.commit()
    db.refresh(offer)

    return offer


@router.patch("/{offer_id}/moderation", response_model=AdminOfferDetail)
def update_offer_moderation(
    offer_id: UUID,
    request: AdminOfferModerationUpdateRequest,
    db: Session = Depends(get_db),
):
    offer = db.get(Offer, offer_id)

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    update_data = request.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(offer, field_name, field_value)

    db.commit()
    db.refresh(offer)

    return offer