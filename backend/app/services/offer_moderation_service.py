import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.offer import Offer, OfferStatus, OfferVisibilityStatus
from app.db.models.deal import Deal, DealStatus
from app.db.models.item import Item, ItemStatus, OwnerType
from app.db.models.item_photo import ItemPhoto
from app.db.models.user_identity import IdentityProvider
from app.schemas.offer import AdminOfferModerationUpdateRequest
from app.services.telegram_notification_service import (
    TelegramNotificationEventService,
    TelegramNotificationService,
)


logger = logging.getLogger(__name__)


class OfferModerationService:
    ALLOWED_MODERATION_FIELDS = {
        "moderated_value",
        "public_value",
        "valuation_source",
        "moderation_comment",
        "visibility_status",
        "sort_priority",
        "is_public",
        "public_comment",
        "participant_visible",
        "participant_public_name",
    }

    def __init__(
        self,
        db: Session,
        notification_service: TelegramNotificationService | None = None,
    ):
        self.db = db
        self.notification_service = notification_service or TelegramNotificationService()

    def moderate_offer(
        self,
        offer_id: UUID,
        request: AdminOfferModerationUpdateRequest,
    ) -> Offer:
        offer_id = self._coerce_uuid(offer_id)
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Offer not found")

        previous_status = offer.status
        previous_is_public = offer.is_public
        previous_public_comment = offer.public_comment

        update_data = request.model_dump(exclude_unset=True)
        allowed_update_data = {
            field_name: field_value
            for field_name, field_value in update_data.items()
            if field_name in self.ALLOWED_MODERATION_FIELDS
            and field_value is not None
        }

        for field_name, field_value in allowed_update_data.items():
            setattr(offer, field_name, field_value)

        if "visibility_status" in allowed_update_data:
            offer.visibility_status = allowed_update_data["visibility_status"].value

        if "is_public" in allowed_update_data:
            if offer.is_public:
                offer.status = OfferStatus.PUBLISHED.value
            elif offer.status == OfferStatus.PUBLISHED.value:
                offer.status = OfferStatus.HIDDEN.value

        self.db.commit()
        self.db.refresh(offer)
        self._notify_user_if_needed(
            offer=offer,
            previous_status=previous_status,
            previous_is_public=previous_is_public,
            previous_public_comment=previous_public_comment,
        )

        return offer

    def select_next_offer(
        self,
        offer_id: UUID,
        *,
        public_story: str | None = None,
        video_url: str | None = None,
        photo_url: str | None = None,
        is_public: bool = True,
    ) -> Deal:
        offer_id = self._coerce_uuid(offer_id)
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Заявка не найдена")

        if offer.status == OfferStatus.SELECTED.value:
            raise ValueError("Заявка уже выбрана в цепочку")

        if offer.status == OfferStatus.REJECTED.value:
            raise ValueError("Отклонённую заявку нельзя выбрать в цепочку")

        existing_deal = self.db.scalar(select(Deal).where(Deal.offer_id == offer_id))

        if existing_deal is not None:
            raise ValueError("По этой заявке уже создан шаг цепочки")

        current_item = self.db.scalar(
            select(Item).where(Item.is_current.is_(True)).with_for_update()
        )

        if current_item is None:
            raise ValueError("Сначала создайте текущий предмет цепочки")

        next_sequence_number = self._get_next_sequence_number()

        item_photos = offer.photos
        item_photo_urls = [photo.photo_url for photo in item_photos] or (
            [photo_url] if photo_url else []
        )

        resulting_item = Item(
            source_offer_id=offer.id,
            user_id=offer.user_id,
            title=offer.title,
            description=offer.description,
            item_type=offer.offer_type,
            internal_value=offer.moderated_value or offer.declared_value,
            valuation_source=offer.valuation_source,
            owner_type=OwnerType.PERSONAL.value,
            owner_name=offer.participant_public_name,
            status=ItemStatus.CURRENT.value,
            sequence_number=next_sequence_number,
            is_current=True,
            is_public=True,
            public_story=public_story or offer.public_comment,
            photo_url=item_photo_urls[0] if item_photo_urls else None,
        )

        current_item.is_current = False
        current_item.status = ItemStatus.PAST.value

        self.db.add(resulting_item)
        self.db.flush()

        if item_photos:
            for index, offer_photo in enumerate(item_photos):
                self.db.add(
                    ItemPhoto(
                        item_id=resulting_item.id,
                        photo_url=offer_photo.photo_url,
                        thumbnail_url=offer_photo.thumbnail_url,
                        width=offer_photo.width,
                        height=offer_photo.height,
                        thumbnail_width=offer_photo.thumbnail_width,
                        thumbnail_height=offer_photo.thumbnail_height,
                        size_bytes=offer_photo.size_bytes,
                        thumbnail_size_bytes=offer_photo.thumbnail_size_bytes,
                        sort_order=index,
                    )
                )
        elif photo_url:
            self.db.add(
                ItemPhoto(
                    item_id=resulting_item.id,
                    photo_url=photo_url,
                    sort_order=0,
                )
            )

        deal = Deal(
            offer_id=offer.id,
            step_number=next_sequence_number,
            given_item_id=current_item.id,
            received_item_id=resulting_item.id,
            status=DealStatus.COMPLETED.value,
            participant_user_id=offer.user_id,
            participant_public_name=offer.participant_public_name,
            participant_visible=offer.participant_visible,
            public_story=public_story or offer.public_comment,
            video_url=video_url,
            is_public=is_public,
        )

        offer.status = OfferStatus.SELECTED.value
        offer.is_public = False

        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)
        TelegramNotificationEventService(
            self.db,
            notification_service=self.notification_service,
        ).send_chain_item_selected_once(
            user_id=offer.user_id,
            entity_id=offer.id,
        )

        return deal

    def update_status(
        self,
        offer_id: UUID,
        status: OfferStatus,
    ) -> Offer:
        offer_id = self._coerce_uuid(offer_id)
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Offer not found")

        previous_status = offer.status
        previous_is_public = offer.is_public
        previous_public_comment = offer.public_comment

        if status == OfferStatus.SELECTED:
            existing_deal = self.db.scalar(select(Deal).where(Deal.offer_id == offer_id))
            if existing_deal is None:
                raise ValueError("Use select-next endpoint to select an offer into the chain")

        offer.status = status.value
        offer.is_public = status == OfferStatus.PUBLISHED
        if status == OfferStatus.HIDDEN:
            offer.visibility_status = OfferVisibilityStatus.HIDDEN.value

        self.db.commit()
        self.db.refresh(offer)
        self._notify_user_if_needed(
            offer=offer,
            previous_status=previous_status,
            previous_is_public=previous_is_public,
            previous_public_comment=previous_public_comment,
        )

        return offer

    def _get_next_sequence_number(self) -> int:
        max_sequence_number = self.db.scalar(select(func.max(Item.sequence_number)))

        if max_sequence_number is not None:
            return max_sequence_number + 1

        max_step_number = self.db.scalar(select(func.max(Deal.step_number))) or 0
        return max_step_number + 1

    @staticmethod
    def _coerce_uuid(value: UUID | str) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    def _notify_user_if_needed(
        self,
        offer: Offer,
        previous_status: str,
        previous_is_public: bool,
        previous_public_comment: str | None,
    ) -> None:
        status_changed = offer.status != previous_status
        public_state_changed = offer.is_public != previous_is_public
        public_comment_changed = offer.public_comment != previous_public_comment

        if not (status_changed or public_state_changed or public_comment_changed):
            return

        telegram_id = self._get_owner_telegram_id(offer)

        if telegram_id is None:
            return

        text = self._build_notification_text(
            offer=offer,
            status_changed=status_changed,
            public_comment_changed=public_comment_changed,
        )

        try:
            self.notification_service.send_telegram_message(telegram_id, text)
        except Exception:
            # Notification delivery must not roll back moderation/status changes.
            logger.exception("Failed to send offer status notification")
            return

    def _get_owner_telegram_id(self, offer: Offer) -> str | None:
        if offer.user is None:
            return None

        for identity in offer.user.identities:
            if identity.provider == IdentityProvider.TELEGRAM.value:
                return identity.provider_user_id

        for account in offer.user.messenger_accounts:
            if account.messenger_type == "telegram":
                return account.external_user_id

        return None

    def _build_notification_text(
        self,
        offer: Offer,
        status_changed: bool,
        public_comment_changed: bool,
    ) -> str:
        if public_comment_changed and not status_changed:
            lines = [f"По офферу «{offer.title}» обновлён комментарий администратора."]
        elif offer.status == OfferStatus.PUBLISHED.value:
            lines = [f"Ваш оффер «{offer.title}» опубликован."]
        elif offer.status == OfferStatus.REJECTED.value:
            lines = [f"Ваш оффер «{offer.title}» отклонён."]
        elif offer.status == OfferStatus.ARCHIVED.value:
            lines = [f"Ваш оффер «{offer.title}» снят с публикации."]
        elif offer.status in {OfferStatus.NEW.value, OfferStatus.MODERATION.value}:
            lines = [f"Ваш оффер «{offer.title}» находится на модерации."]
        elif offer.status == OfferStatus.APPROVED.value:
            lines = [f"Ваш оффер «{offer.title}» одобрен."]
        else:
            lines = [f"Статус оффера «{offer.title}» изменён: {offer.status_label}."]

        if offer.public_comment:
            lines.append(f"Комментарий администратора: {offer.public_comment}")

        return "\n".join(lines)
