from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.deal import Deal
from app.db.models.item import Item
from app.schemas.deal import AdminDealCreateRequest


class DealService:
    def __init__(self, db: Session):
        self.db = db

    def create_deal(self, request: AdminDealCreateRequest) -> Deal:
        given_item = self.db.get(Item, request.given_item_id)

        if given_item is None:
            raise ValueError("Предмет, который отдаём, не найден")

        if not given_item.is_current:
            raise ValueError("Обмен можно создать только от текущего предмета цепочки")

        max_step_number = self.db.scalar(select(func.max(Deal.step_number))) or 0
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

        self.db.add(received_item)
        self.db.flush()

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

        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)

        return deal