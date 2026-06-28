from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased, selectinload

from app.api.deps import get_db
from app.db.models.deal import Deal, DealStatus
from app.db.models.item import Item
from app.schemas.deal import PublicExchangeChainDealItem, PublicExchangeChainItem
from app.schemas.item import PublicCurrentItemResponse, PublicItemDetailResponse

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


@router.get("/current-item", response_model=PublicCurrentItemResponse)
def get_current_item(
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(Item).where(
            Item.is_current.is_(True),
            Item.is_public.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Текущий предмет пока не опубликован",
        )

    return item


@router.get("/exchange-chain", response_model=list[PublicExchangeChainItem])
def get_exchange_chain(
    db: Session = Depends(get_db),
):
    given_item = aliased(Item)
    received_item = aliased(Item)

    rows = (
        db.execute(
            select(Deal, given_item, received_item)
            .join(given_item, Deal.given_item_id == given_item.id)
            .join(received_item, Deal.received_item_id == received_item.id)
            .where(
                Deal.is_public.is_(True),
                Deal.status == DealStatus.COMPLETED.value,
                given_item.is_public.is_(True),
                received_item.is_public.is_(True),
            )
            .order_by(Deal.step_number.asc())
        )
        .tuples()
        .all()
    )

    return [
        PublicExchangeChainItem(
            id=deal.id,
            step_number=deal.step_number,
            status=deal.status,
            public_story=deal.public_story,
            video_url=deal.video_url,
            participant_public_name=(
                deal.participant_public_name if deal.participant_visible else None
            ),
            participant_visible=deal.participant_visible,
            deal_date=deal.deal_date,
            given_item=PublicExchangeChainDealItem(
                id=deal_given_item.id,
                title=deal_given_item.title,
                description=deal_given_item.description,
                photo_url=deal_given_item.photo_url,
                photo_urls=deal_given_item.photo_urls,
            ),
            received_item=PublicExchangeChainDealItem(
                id=deal_received_item.id,
                title=deal_received_item.title,
                description=deal_received_item.description,
                photo_url=deal_received_item.photo_url,
                photo_urls=deal_received_item.photo_urls,
            ),
        )
        for deal, deal_given_item, deal_received_item in rows
    ]


@router.get("/items/{item_id}", response_model=PublicItemDetailResponse)
def get_public_item(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(Item)
        .options(selectinload(Item.photos))
        .where(
            Item.id == item_id,
            Item.is_public.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )

    return item
