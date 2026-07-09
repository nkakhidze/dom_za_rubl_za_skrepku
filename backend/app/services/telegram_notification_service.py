import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from urllib import request
from urllib.error import HTTPError, URLError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.telegram_notification_event import (
    TelegramNotificationEvent,
    TelegramNotificationStatus,
)
from app.db.models.user_identity import IdentityProvider, UserIdentity


logger = logging.getLogger(__name__)


class TelegramNotificationService:
    def __init__(
        self,
        bot_token: str | None = None,
        timeout_seconds: int = 10,
    ):
        self.bot_token = bot_token if bot_token is not None else settings.telegram_bot_token
        self.timeout_seconds = timeout_seconds

    def send_telegram_message(self, telegram_id: str, text: str) -> bool:
        if not self.bot_token or self.bot_token == "change_me":
            logger.warning("Telegram bot token is not configured; notification skipped")
            return False

        payload = json.dumps(
            {
                "chat_id": telegram_id,
                "text": text,
            }
        ).encode("utf-8")

        telegram_request = request.Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(telegram_request, timeout=self.timeout_seconds):
                return True
        except (HTTPError, URLError, TimeoutError, OSError):
            logger.exception("Failed to send Telegram notification")
            return False


class TelegramNotificationEventService:
    CHAIN_ITEM_SELECTED = "chain_item_selected"

    def __init__(
        self,
        db: Session,
        notification_service: TelegramNotificationService | None = None,
    ):
        self.db = db
        self.notification_service = notification_service or TelegramNotificationService()

    def send_chain_item_selected_once(
        self,
        *,
        user_id: UUID,
        entity_id: UUID,
    ) -> None:
        existing_event = self.db.scalar(
            select(TelegramNotificationEvent).where(
                TelegramNotificationEvent.event_type == self.CHAIN_ITEM_SELECTED,
                TelegramNotificationEvent.entity_type == "offer",
                TelegramNotificationEvent.entity_id == entity_id,
                TelegramNotificationEvent.user_id == user_id,
            )
        )

        if existing_event is not None:
            return

        event = TelegramNotificationEvent(
            user_id=user_id,
            event_type=self.CHAIN_ITEM_SELECTED,
            entity_type="offer",
            entity_id=entity_id,
            status=TelegramNotificationStatus.PENDING,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        identity = self.db.scalar(
            select(UserIdentity).where(
                UserIdentity.user_id == user_id,
                UserIdentity.provider == IdentityProvider.TELEGRAM.value,
            )
        )

        if identity is None:
            return

        text = (
            "Ваш предмет включён в цепочку обмена!\n"
            "Спасибо за участие в проекте «Дом за скрепку». "
            "Вместе мы приближаемся к восстановлению исторического дома."
        )

        try:
            delivered = self.notification_service.send_telegram_message(
                identity.provider_user_id,
                text,
            )
        except Exception as exc:
            logger.exception("Failed to send chain item Telegram notification")
            event.status = TelegramNotificationStatus.FAILED
            event.last_error = str(exc)
            self.db.commit()
            return

        if delivered:
            event.status = TelegramNotificationStatus.SENT
            event.sent_at = datetime.now(timezone.utc)
            event.last_error = None
        else:
            event.status = TelegramNotificationStatus.FAILED
            event.last_error = "Telegram API returned an error"

        self.db.commit()
