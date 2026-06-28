import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.messenger_account import MessengerType
from app.db.models.offer import Offer, OfferStatus
from app.schemas.offer import AdminOfferModerationUpdateRequest
from app.services.telegram_notification_service import TelegramNotificationService


logger = logging.getLogger(__name__)


class OfferModerationService:
    ALLOWED_MODERATION_FIELDS = {
        "moderated_value",
        "public_value",
        "valuation_source",
        "moderation_comment",
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
        }

        for field_name, field_value in allowed_update_data.items():
            setattr(offer, field_name, field_value)

        if "is_public" in allowed_update_data:
            if offer.is_public:
                offer.status = OfferStatus.PUBLISHED.value
            elif offer.status == OfferStatus.PUBLISHED.value:
                offer.status = OfferStatus.ARCHIVED.value

        self.db.commit()
        self.db.refresh(offer)
        self._notify_user_if_needed(
            offer=offer,
            previous_status=previous_status,
            previous_is_public=previous_is_public,
            previous_public_comment=previous_public_comment,
        )

        return offer

    def update_status(
        self,
        offer_id: UUID,
        status: OfferStatus,
    ) -> Offer:
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Offer not found")

        previous_status = offer.status
        previous_is_public = offer.is_public
        previous_public_comment = offer.public_comment

        offer.status = status.value
        offer.is_public = status == OfferStatus.PUBLISHED

        self.db.commit()
        self.db.refresh(offer)
        self._notify_user_if_needed(
            offer=offer,
            previous_status=previous_status,
            previous_is_public=previous_is_public,
            previous_public_comment=previous_public_comment,
        )

        return offer

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

        for account in offer.user.messenger_accounts:
            if account.messenger_type == MessengerType.TELEGRAM.value:
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
