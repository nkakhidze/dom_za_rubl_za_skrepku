from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.db.models.messenger_account import MessengerAccount, MessengerType
from app.db.models.offer import Offer
from app.db.models.user import User
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
