from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.deal import Deal, DealStatus
from app.db.models.item import Item, ItemStatus
from app.db.models.messenger_account import MessengerType
from app.db.models.user import User
from app.db.models.offer import Offer, OfferStatus
from app.schemas.deal import (
    AdminDealCreateFromOfferRequest,
    AdminDealCreateRequest,
    DealCreateRequest,
)
from app.services.telegram_notification_service import TelegramNotificationService
from app.services.offer_moderation_service import OfferModerationService



class DealService:
    ACTIVE_DEAL_STATUSES = {
        DealStatus.NEW.value,
        DealStatus.ACCEPTED.value,
    }

    def __init__(
        self,
        db: Session,
        notification_service: TelegramNotificationService | None = None,
    ):
        self.db = db
        self.notification_service = notification_service or TelegramNotificationService()

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
            status=DealStatus.COMPLETED.value,
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
        return OfferModerationService(self.db, self.notification_service).select_next_offer(
            offer_id,
            public_story=request.public_story,
            video_url=request.video_url,
            photo_url=request.photo_url,
            is_public=request.is_public,
        )

    def create_response_deal(self, request: DealCreateRequest) -> Deal:
        offer = self.db.get(Offer, request.offer_id)

        if offer is None:
            raise ValueError("Offer not found")

        if not offer.is_public or offer.status != OfferStatus.PUBLISHED.value:
            raise ValueError("Offer is not public")

        item = self.db.get(Item, request.item_id)

        if item is None:
            raise ValueError("Item not found")

        if item.status != ItemStatus.ACTIVE.value:
            raise ValueError("Item is not active")

        if item.user_id is None:
            raise ValueError("Item has no owner")

        if item.user_id == offer.user_id:
            raise ValueError("Cannot create a deal for your own offer")

        existing_active_deal = self.db.scalar(
            select(Deal).where(
                Deal.offer_id == request.offer_id,
                Deal.given_item_id == request.item_id,
                Deal.status.in_(self.ACTIVE_DEAL_STATUSES),
            )
        )

        if existing_active_deal is not None:
            raise ValueError("Active deal already exists")

        deal = Deal(
            offer_id=offer.id,
            step_number=self._get_next_step_number(),
            given_item_id=item.id,
            received_item_id=item.id,
            participant_user_id=item.user_id,
            participant_public_name=item.owner_name,
            participant_visible=False,
            status=DealStatus.NEW.value,
            is_public=False,
        )

        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)
        self._notify_offer_owner_about_new_deal(offer)

        return deal

    def update_status(self, deal_id: UUID, status: DealStatus) -> Deal:
        deal = self.db.get(Deal, deal_id)

        if deal is None:
            raise ValueError("Deal not found")

        previous_status = deal.status
        deal.status = status.value

        self.db.commit()
        self.db.refresh(deal)

        if previous_status != deal.status:
            self._notify_deal_participants_about_status(deal)

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

    def _notify_offer_owner_about_new_deal(self, offer: Offer) -> None:
        telegram_id = self._get_user_telegram_id(offer.user)

        if telegram_id is None:
            return

        self._send_notification(
            telegram_id,
            f"На ваш оффер «{offer.title}» появился новый отклик.",
        )

    def _notify_deal_participants_about_status(self, deal: Deal) -> None:
        item = self.db.get(Item, deal.given_item_id)
        offer = self.db.get(Offer, deal.offer_id) if deal.offer_id is not None else None

        offer_title = offer.title if offer is not None else "оффер"
        item_owner_message = self._build_item_owner_status_message(deal, offer_title)
        offer_owner_message = self._build_offer_owner_status_message(deal, offer_title)

        if item is not None:
            item_owner_id = self._get_user_telegram_id(item.user)

            if item_owner_id is not None:
                self._send_notification(item_owner_id, item_owner_message)

        if offer is not None:
            offer_owner_id = self._get_user_telegram_id(offer.user)

            if offer_owner_id is not None:
                self._send_notification(offer_owner_id, offer_owner_message)

    def _build_item_owner_status_message(self, deal: Deal, offer_title: str) -> str:
        if deal.status == DealStatus.ACCEPTED.value:
            return f"Ваш отклик на оффер «{offer_title}» принят."

        if deal.status == DealStatus.REJECTED.value:
            return f"Ваш отклик на оффер «{offer_title}» отклонён."

        if deal.status == DealStatus.COMPLETED.value:
            return f"Сделка по офферу «{offer_title}» завершена."

        if deal.status == DealStatus.CANCELLED.value:
            return f"Сделка по офферу «{offer_title}» отменена."

        return f"Статус вашей заявки на обмен изменён: {deal.status_label}."

    def _build_offer_owner_status_message(self, deal: Deal, offer_title: str) -> str:
        if deal.status == DealStatus.ACCEPTED.value:
            return f"Вы приняли отклик по офферу «{offer_title}»."

        if deal.status == DealStatus.REJECTED.value:
            return f"Отклик по офферу «{offer_title}» отклонён."

        if deal.status == DealStatus.COMPLETED.value:
            return f"Сделка по офферу «{offer_title}» завершена."

        if deal.status == DealStatus.CANCELLED.value:
            return f"Сделка по офферу «{offer_title}» отменена."

        return f"Статус отклика по офферу «{offer_title}» изменён: {deal.status_label}."

    def _get_user_telegram_id(self, user: User | None) -> str | None:
        if user is None:
            return None

        for account in user.messenger_accounts:
            if account.messenger_type == MessengerType.TELEGRAM.value:
                return account.external_user_id

        return None

    def _send_notification(self, telegram_id: str, text: str) -> None:
        try:
            self.notification_service.send_telegram_message(telegram_id, text)
        except Exception:
            return
