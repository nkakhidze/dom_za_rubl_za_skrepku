from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.deal import Deal
from app.db.models.item import Item
from app.db.models.user import User
from app.db.models.offer import Offer, OfferStatus
from app.schemas.deal import AdminDealCreateFromOfferRequest, AdminDealCreateRequest



class DealService:
    def __init__(self, db: Session):
        self.db = db

    def create_deal(self, request: AdminDealCreateRequest) -> Deal:
        given_item = self._get_current_given_item(request.given_item_id)

        next_step_number = self._get_next_step_number()

        if request.participant_user_id is not None:
            participant = self.db.get(User, request.participant_user_id)

            if participant is None:
                raise ValueError("Указанный participant_user_id не найден")

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

    def create_deal_from_offer(
        self,
        offer_id: UUID,
        request: AdminDealCreateFromOfferRequest,
    ) -> Deal:
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Заявка не найдена")

        if offer.status in {
            OfferStatus.REJECTED.value,
            OfferStatus.CANCELLED.value,
            OfferStatus.COMPLETED.value,
        }:
            raise ValueError("По заявке с таким статусом нельзя создать обмен")

        existing_deal = self.db.scalar(
            select(Deal).where(Deal.offer_id == offer_id)
        )

        if existing_deal is not None:
            raise ValueError("По этой заявке уже создан обмен")

        given_item = self._get_current_given_item(request.given_item_id)

        next_step_number = self._get_next_step_number()

        received_item = Item(
            title=offer.title,
            description=offer.description,
            item_type=offer.offer_type,
            internal_value=offer.moderated_value or offer.declared_value,
            valuation_source=offer.valuation_source,
            owner_type=request.owner_type.value,
            owner_name=request.owner_name,
            is_current=True,
            is_public=True,
            public_story=request.public_story or offer.public_comment,
            photo_url=request.photo_url,
        )

        given_item.is_current = False

        self.db.add(received_item)
        self.db.flush()

        deal = Deal(
            offer_id=offer.id,
            step_number=next_step_number,
            given_item_id=given_item.id,
            received_item_id=received_item.id,
            participant_user_id=offer.user_id,
            participant_public_name=offer.participant_public_name,
            participant_visible=offer.participant_visible,
            public_story=request.public_story or offer.public_comment,
            video_url=request.video_url,
            is_public=request.is_public,
        )

        offer.status = OfferStatus.COMPLETED.value

        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)

        return deal

    def _get_current_given_item(self, given_item_id: UUID) -> Item:
        given_item = self.db.get(Item, given_item_id)

        if given_item is None:
            raise ValueError("Предмет, который отдаём, не найден")

        if not given_item.is_current:
            raise ValueError("Обмен можно создать только от текущего предмета цепочки")

        return given_item

    def _get_next_step_number(self) -> int:
        max_step_number = self.db.scalar(select(func.max(Deal.step_number))) or 0
        return max_step_number + 1