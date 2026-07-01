import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.account_link_token import AccountLinkToken
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.db.models.messenger_account import MessengerAccount, MessengerType
from app.db.models.offer import Offer
from app.db.models.user import User
from app.db.models.user_identity import IdentityProvider, UserIdentity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_telegram_display_name(
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> str | None:
    full_name = " ".join(part for part in [first_name, last_name] if part)
    return full_name or username


def hash_link_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TelegramUserPayload:
    telegram_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


@dataclass(frozen=True)
class ResolveTelegramUserResult:
    user: User
    identity: UserIdentity
    created: bool


@dataclass(frozen=True)
class AccountLinkResult:
    user: User
    identity: UserIdentity
    merged_user_id: UUID | None
    already_linked: bool = False


class AccountLinkError(ValueError):
    pass


class AccountLinkConflictError(AccountLinkError):
    pass


class UserIdentityService:
    LINK_TOKEN_TTL_MINUTES = 15

    def __init__(self, db: Session):
        self.db = db

    def resolve_telegram_user(
        self,
        payload: TelegramUserPayload,
        *,
        commit: bool = True,
    ) -> ResolveTelegramUserResult:
        now = utc_now()
        display_name = build_telegram_display_name(
            payload.first_name,
            payload.last_name,
            payload.username,
        )

        identity = self.db.scalar(
            select(UserIdentity).where(
                UserIdentity.provider == IdentityProvider.TELEGRAM.value,
                UserIdentity.provider_user_id == payload.telegram_user_id,
            )
        )

        if identity is not None:
            identity.username = payload.username
            identity.display_name = display_name
            identity.language_code = payload.language_code
            identity.last_seen_at = now
            if identity.user.display_name is None and display_name:
                identity.user.display_name = display_name
            self._ensure_legacy_messenger_account(identity.user, payload)
            if commit:
                self.db.commit()
                self.db.refresh(identity.user)
            return ResolveTelegramUserResult(identity.user, identity, created=False)

        user = User(display_name=display_name)
        self.db.add(user)
        self.db.flush()

        identity = UserIdentity(
            user_id=user.id,
            provider=IdentityProvider.TELEGRAM.value,
            provider_user_id=payload.telegram_user_id,
            username=payload.username,
            display_name=display_name,
            language_code=payload.language_code,
            last_seen_at=now,
        )
        self.db.add(identity)
        self._ensure_legacy_messenger_account(user, payload)

        if commit:
            self.db.commit()
            self.db.refresh(user)

        return ResolveTelegramUserResult(user, identity, created=True)

    def create_telegram_link(self, user: User) -> dict[str, str]:
        existing_identity = self.get_user_telegram_identity(user.id)
        if existing_identity is not None:
            return {
                "status": "connected",
                "telegram_username": existing_identity.username or "",
                "deep_link": "",
            }

        raw_token = secrets.token_urlsafe(32)
        link_token = AccountLinkToken(
            user_id=user.id,
            provider=IdentityProvider.TELEGRAM.value,
            token_hash=hash_link_token(raw_token),
            expires_at=utc_now() + timedelta(minutes=self.LINK_TOKEN_TTL_MINUTES),
        )
        self.db.add(link_token)
        self.db.commit()

        bot_username = (settings.telegram_bot_username or "").lstrip("@")
        deep_link = f"https://t.me/{bot_username}?start=link_{raw_token}" if bot_username else ""
        return {
            "status": "pending",
            "telegram_username": "",
            "deep_link": deep_link,
        }

    def get_user_telegram_identity(self, user_id: UUID) -> UserIdentity | None:
        return self.db.scalar(
            select(UserIdentity).where(
                UserIdentity.user_id == user_id,
                UserIdentity.provider == IdentityProvider.TELEGRAM.value,
            )
        )

    def consume_telegram_link(
        self,
        raw_token: str,
        payload: TelegramUserPayload,
    ) -> AccountLinkResult:
        token = self.db.scalar(
            select(AccountLinkToken).where(
                AccountLinkToken.provider == IdentityProvider.TELEGRAM.value,
                AccountLinkToken.token_hash == hash_link_token(raw_token),
            )
        )

        if token is None or self._is_expired(token.expires_at):
            raise AccountLinkError("Ссылка недействительна или устарела")

        site_user = self.db.get(User, token.user_id)
        if site_user is None:
            raise AccountLinkError("Пользователь сайта не найден")

        existing_site_identity = self.get_user_telegram_identity(site_user.id)
        if existing_site_identity is not None:
            if existing_site_identity.provider_user_id == payload.telegram_user_id:
                token.used_at = token.used_at or utc_now()
                self.db.commit()
                return AccountLinkResult(site_user, existing_site_identity, None, already_linked=True)
            raise AccountLinkConflictError("К этому аккаунту сайта уже привязан другой Telegram")

        result = self.resolve_telegram_user(payload, commit=False)
        telegram_user = result.user
        identity = result.identity

        if telegram_user.id == site_user.id:
            token.used_at = token.used_at or utc_now()
            self.db.commit()
            return AccountLinkResult(site_user, identity, None, already_linked=True)

        identity.user_id = site_user.id
        self._move_user_data(telegram_user.id, site_user.id)
        telegram_user.merged_into_user_id = site_user.id
        telegram_user.merged_at = utc_now()
        telegram_user.is_active = False
        token.used_at = token.used_at or utc_now()
        self._ensure_legacy_messenger_account(site_user, payload)
        self.db.commit()
        self.db.refresh(site_user)
        return AccountLinkResult(site_user, identity, telegram_user.id)

    def _move_user_data(self, source_user_id: UUID, target_user_id: UUID) -> None:
        self.db.query(Offer).filter(Offer.user_id == source_user_id).update(
            {Offer.user_id: target_user_id},
            synchronize_session=False,
        )
        self.db.query(Item).filter(Item.user_id == source_user_id).update(
            {Item.user_id: target_user_id},
            synchronize_session=False,
        )
        self.db.query(Deal).filter(Deal.participant_user_id == source_user_id).update(
            {Deal.participant_user_id: target_user_id},
            synchronize_session=False,
        )

    def _ensure_legacy_messenger_account(
        self,
        user: User,
        payload: TelegramUserPayload,
    ) -> None:
        account = self.db.scalar(
            select(MessengerAccount).where(
                MessengerAccount.messenger_type == MessengerType.TELEGRAM.value,
                MessengerAccount.external_user_id == payload.telegram_user_id,
            )
        )

        if account is None:
            self.db.add(
                MessengerAccount(
                    user_id=user.id,
                    messenger_type=MessengerType.TELEGRAM.value,
                    external_user_id=payload.telegram_user_id,
                    username=payload.username,
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                )
            )
            return

        account.user_id = user.id
        account.username = payload.username
        account.first_name = payload.first_name
        account.last_name = payload.last_name

    @staticmethod
    def _is_expired(expires_at: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at < utc_now()
