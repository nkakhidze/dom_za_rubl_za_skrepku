from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_admin_access, require_any_role
from app.db.models.auth import RoleCode
from app.db.models.offer import Offer
from app.db.models.offer_photo import OfferPhoto
from app.schemas.offer import (
    AdminOfferDetail,
    AdminOfferListItem,
    AdminOfferModerationUpdateRequest,
    AdminOfferStatusUpdateRequest,
    AdminOfferPhotoResponse,
)
from app.services.offer_moderation_service import OfferModerationService

router = APIRouter(
    prefix="/admin/offers",
    tags=["admin offers"],
    dependencies=[Depends(require_admin_access)],
)


@router.get("", response_model=list[AdminOfferListItem])
def get_offers(
    db: Session = Depends(get_db),
    offer_status: str | None = Query(default=None, description="Фильтр по статусу заявки"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
        .order_by(Offer.created_at.desc())
    )

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
    offer = db.scalar(
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(Offer.id == offer_id)
    )

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    return offer


@router.patch(
    "/{offer_id}/status",
    response_model=AdminOfferDetail,
    dependencies=[Depends(require_any_role(RoleCode.MODERATOR.value, RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def update_offer_status(
    offer_id: UUID,
    request: AdminOfferStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    service = OfferModerationService(db)

    try:
        return service.update_status(offer_id, request.status)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{offer_id}/moderation",
    response_model=AdminOfferDetail,
    dependencies=[Depends(require_any_role(RoleCode.MODERATOR.value, RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def update_offer_moderation(
    offer_id: UUID,
    request: AdminOfferModerationUpdateRequest,
    db: Session = Depends(get_db),
):
    service = OfferModerationService(db)

    try:
        return service.moderate_offer(offer_id, request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get("/{offer_id}/photos", response_model=list[AdminOfferPhotoResponse])
def get_offer_photos(
    offer_id: UUID,
    db: Session = Depends(get_db),
):
    offer = db.get(Offer, offer_id)

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    query = select(OfferPhoto).where(OfferPhoto.offer_id == offer_id)

    return db.scalars(query).all()
