from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.schemas.deal import AdminDealCreateRequest, AdminDealResponse

router = APIRouter(
    prefix="/admin/deals",
    tags=["admin deals"],
)


@router.post("", response_model=AdminDealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(
    request: AdminDealCreateRequest,
    db: Session = Depends(get_db),
):
    given_item = db.get(Item, request.given_item_id)

    if given_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет, который отдаём, не найден",
        )

    if not given_item.is_current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обмен можно создать только от текущего предмета цепочки",
        )

    max_step_number = db.scalar(select(func.max(Deal.step_number))) or 0
    next_step_number = max_step_number + 1

    received_item = Item(
        title=request.received_item_title,
        description=request.received_item_description,
        item_type=request.received_item_type.value,
        internal_value=request.received_item_internal_value,
        valuation_source=request.received_item_valuation_source,
        owner_type=request.owner_type.value,
        owner_name=request.owner_name,
        is_current=True,
        is_public=True,
        public_story=request.public_story,
        photo_url=request.photo_url,
    )

    given_item.is_current = False

    db.add(received_item)
    db.flush()

    deal = Deal(
        step_number=next_step_number,
        given_item_id=given_item.id,
        received_item_id=received_item.id,
        participant_user_id=request.participant_user_id,
        participant_public_name=request.participant_public_name,
        participant_visible=request.participant_visible,
        public_story=request.public_story,
        video_url=request.video_url,
        is_public=request.is_public,
    )

    db.add(deal)
    db.commit()
    db.refresh(deal)

    return deal


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