from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_admin_access, require_any_role
from app.db.models.auth import RoleCode
from app.db.models.offer import Offer, OfferStatus
from app.db.models.offer_photo import OfferPhoto
from app.schemas.offer import (
    AdminOfferDetail,
    AdminOfferListItem,
    AdminOfferModerationUpdateRequest,
    AdminOfferSelectNextRequest,
    AdminOfferStatusUpdateRequest,
    AdminOfferPhotoResponse,
)
from app.services.offer_moderation_service import OfferModerationService
from app.schemas.deal import AdminDealResponse

router = APIRouter(
    prefix="/admin/offers",
    tags=["admin offers"],
    dependencies=[Depends(require_admin_access)],
)


@router.get("", response_model=list[AdminOfferListItem])
def get_offers(
    db: Session = Depends(get_db),
    offer_status: str | None = Query(default=None, description="Фильтр по статусу заявки"),
    visibility_status: list[str] | None = Query(default=None, description="Фильтр по видимости заявки"),
    sort: str = Query(default="value_desc", description="value_desc|created_at_desc|moderated_value_desc|priority"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
    )

    if offer_status is not None:
        query = query.where(Offer.status == offer_status)
    else:
        query = query.where(Offer.status != OfferStatus.SELECTED.value)

    if visibility_status is not None:
        query = query.where(Offer.visibility_status.in_(visibility_status))

    user_value_for_sort = case(
        (Offer.moderated_value.is_(None), Offer.declared_value),
        (Offer.declared_value <= Offer.moderated_value, Offer.declared_value),
        else_=None,
    )

    if sort in {"value_desc", "moderated_value_desc"}:
        query = query.order_by(
            Offer.visibility_status.asc(),
            Offer.moderated_value.desc().nullslast(),
            user_value_for_sort.desc().nullslast(),
            Offer.created_at.desc(),
        )
    elif sort == "priority":
        query = query.order_by(
            Offer.visibility_status.asc(),
            Offer.sort_priority.desc(),
            Offer.created_at.desc(),
        )
    else:
        query = query.order_by(Offer.created_at.desc())

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


@router.post(
    "/{offer_id}/select-next",
    response_model=AdminDealResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role(RoleCode.MODERATOR.value, RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def select_offer_as_next_item(
    offer_id: UUID,
    request: AdminOfferSelectNextRequest,
    db: Session = Depends(get_db),
):
    service = OfferModerationService(db)

    try:
        return service.select_next_offer(
            offer_id,
            public_story=request.public_story,
            video_url=request.video_url,
            photo_url=request.photo_url,
            is_public=request.is_public,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
