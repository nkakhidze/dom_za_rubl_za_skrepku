from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_db
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.schemas.deal import PublicExchangeChainItem
from app.schemas.item import PublicCurrentItemResponse

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

    rows = db.execute(
        select(
            Deal.step_number,
            given_item.title.label("given_item_title"),
            received_item.title.label("received_item_title"),
            Deal.public_story,
            Deal.video_url,
            Deal.participant_public_name,
            Deal.participant_visible,
            Deal.deal_date,
        )
        .join(given_item, Deal.given_item_id == given_item.id)
        .join(received_item, Deal.received_item_id == received_item.id)
        .where(
            Deal.is_public.is_(True),
            given_item.is_public.is_(True),
            received_item.is_public.is_(True),
        )
        .order_by(Deal.step_number.asc())
    ).mappings().all()

    return rows