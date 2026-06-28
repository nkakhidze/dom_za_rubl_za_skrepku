from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin_access, require_any_role
from app.db.models.auth import RoleCode
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.db.models.offer import Offer
from app.db.models.user import User
from app.schemas.deal import (
    AdminDealCreateFromOfferRequest,
    AdminDealCreateRequest,
    AdminDealDetail,
    AdminDealItemDetail,
    AdminDealListItem,
    AdminDealOfferDetail,
    AdminDealResponse,
    AdminDealStatusUpdateRequest,
    AdminDealUserResponse,
)
from app.services.deal_service import DealService

router = APIRouter(
    prefix="/admin/deals",
    tags=["admin deals"],
    dependencies=[Depends(require_admin_access)],
)


def _admin_user_response(user: User | None) -> AdminDealUserResponse | None:
    if user is None:
        return None

    return AdminDealUserResponse(
        id=user.id,
        display_name=user.display_name,
        phone=user.phone,
        messenger_accounts=list(user.messenger_accounts),
    )


def _admin_deal_list_item(deal: Deal, db: Session) -> AdminDealListItem | None:
    item = db.get(Item, deal.given_item_id)

    if item is None:
        return None

    offer = db.get(Offer, deal.offer_id) if deal.offer_id is not None else None
    offer_owner = offer.user if offer is not None else None
    item_owner = item.user

    return AdminDealListItem(
        deal_id=deal.id,
        deal_status=deal.status,
        deal_status_label=deal.status_label,
        deal_created_at=deal.created_at,
        offer_id=deal.offer_id,
        offer_title=offer.title if offer is not None else None,
        offer_status=offer.status if offer is not None else None,
        offer_is_public=offer.is_public if offer is not None else None,
        offer_owner_user_id=offer.user_id if offer is not None else None,
        offer_owner_display_name=offer_owner.display_name if offer_owner is not None else None,
        item_id=item.id,
        item_title=item.title,
        item_status=item.status,
        item_owner_user_id=item.user_id,
        item_owner_display_name=item_owner.display_name if item_owner is not None else None,
    )


def _admin_deal_detail(deal: Deal, db: Session) -> AdminDealDetail:
    item = db.get(Item, deal.given_item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deal has no linked item",
        )

    offer = db.get(Offer, deal.offer_id) if deal.offer_id is not None else None

    return AdminDealDetail(
        id=deal.id,
        status=deal.status,
        status_label=deal.status_label,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
        offer=AdminDealOfferDetail(
            id=offer.id,
            title=offer.title,
            description=offer.description,
            city=offer.city,
            public_value=offer.public_value,
            status=offer.status,
            is_public=offer.is_public,
            photo_urls=offer.photo_urls,
        )
        if offer is not None
        else None,
        item=AdminDealItemDetail(
            id=item.id,
            title=item.title,
            description=item.description,
            status=item.status,
        ),
        offer_owner=_admin_user_response(offer.user if offer is not None else None),
        item_owner=_admin_user_response(item.user),
    )


@router.get("", response_model=list[AdminDealListItem])
def get_deals(
    db: Session = Depends(get_db),
    is_public: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Deal).order_by(Deal.step_number.asc())

    if is_public is not None:
        query = query.where(Deal.is_public == is_public)

    return [
        deal_item
        for deal_item in (
            _admin_deal_list_item(deal, db)
            for deal in db.scalars(query.limit(limit).offset(offset)).all()
        )
        if deal_item is not None
    ]


@router.get("/{deal_id}", response_model=AdminDealDetail)
def get_deal(
    deal_id: UUID,
    db: Session = Depends(get_db),
):
    deal = db.get(Deal, deal_id)

    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    return _admin_deal_detail(deal, db)


@router.patch(
    "/{deal_id}/status",
    response_model=AdminDealDetail,
    dependencies=[Depends(require_any_role(RoleCode.MODERATOR.value, RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def update_deal_status(
    deal_id: UUID,
    request: AdminDealStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    service = DealService(db)

    try:
        deal = service.update_status(deal_id, request.status)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return _admin_deal_detail(deal, db)


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


