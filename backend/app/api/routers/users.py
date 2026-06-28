from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.core.config import settings
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.db.models.messenger_account import MessengerAccount, MessengerType
from app.db.models.offer import Offer
from app.db.models.user import User
from app.schemas.deal import UserDealListItem
from app.schemas.auth import PhoneUpdateRequest
from app.schemas.item import UserItemResponse
from app.schemas.offer import UserOfferListItem
from app.schemas.user import TelegramUserCreateRequest, TelegramUserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/telegram", response_model=TelegramUserResponse)
def create_or_get_telegram_user(
    request: TelegramUserCreateRequest,
    db: Session = Depends(get_db),
):
    messenger_account = db.scalar(
        select(MessengerAccount).where(
            MessengerAccount.messenger_type == MessengerType.TELEGRAM.value,
            MessengerAccount.external_user_id == request.telegram_id,
        )
    )

    if messenger_account is not None:
        user = db.get(User, messenger_account.user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Messenger account has no linked user",
            )

        if request.display_name and user.display_name != request.display_name:
            user.display_name = request.display_name
            db.commit()
            db.refresh(user)

        return TelegramUserResponse(
            id=user.id,
            telegram_id=request.telegram_id,
            display_name=user.display_name,
        )

    user = User(display_name=request.display_name)
    db.add(user)
    db.flush()

    db.add(
        MessengerAccount(
            user_id=user.id,
            messenger_type=MessengerType.TELEGRAM.value,
            external_user_id=request.telegram_id,
        )
    )
    db.commit()
    db.refresh(user)

    return TelegramUserResponse(
        id=user.id,
        telegram_id=request.telegram_id,
        display_name=user.display_name,
    )


@router.get("/{user_id}/offers", response_model=list[UserOfferListItem])
def get_user_offers(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(Offer.user_id == user_id)
        .order_by(Offer.created_at.desc())
    )

    return db.scalars(query).all()


@router.get("/{user_id}/items", response_model=list[UserItemResponse])
def get_user_items(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    query = (
        select(Item)
        .where(Item.user_id == user_id)
        .order_by(Item.created_at.desc())
    )

    return db.scalars(query).all()


@router.get("/{user_id}/deals", response_model=list[UserDealListItem])
def get_user_deals(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    owned_item_ids = select(Item.id).where(Item.user_id == user_id)
    owned_offer_ids = select(Offer.id).where(Offer.user_id == user_id)

    query = (
        select(Deal)
        .where(
            or_(
                Deal.given_item_id.in_(owned_item_ids),
                Deal.offer_id.in_(owned_offer_ids),
            )
        )
        .order_by(Deal.created_at.desc())
    )

    user_deals = []

    for deal in db.scalars(query).all():
        offer = db.get(Offer, deal.offer_id) if deal.offer_id is not None else None
        item = db.get(Item, deal.given_item_id)

        if item is None:
            continue

        user_deals.append(
            UserDealListItem(
                id=deal.id,
                status=deal.status,
                status_label=deal.status_label,
                offer_id=deal.offer_id,
                offer_title=offer.title if offer is not None else None,
                item_id=item.id,
                item_title=item.title,
                created_at=deal.created_at,
            )
        )

    return user_deals


@router.post("/{user_id}/phone")
def set_user_phone(
    user_id: UUID,
    request: PhoneUpdateRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.phone = request.phone
    user.phone_verified = False
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "phone": user.phone,
        "phone_verified": user.phone_verified,
    }


@router.post("/{user_id}/phone/verify-dev")
def verify_user_phone_dev(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    if not settings.dev_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.phone_verified = True
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "phone": user.phone,
        "phone_verified": user.phone_verified,
    }
