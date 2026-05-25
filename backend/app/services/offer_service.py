from datetime import datetime, time, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.messenger_account import MessengerAccount
from app.db.models.offer import ContractStatus, Offer, OfferStatus, OfferType
from app.db.models.offer_photo import OfferPhoto
from app.db.models.user import User
from app.schemas.offer import OfferCreateRequest
from app.services.offer_limit_service import OfferLimitResult, OfferLimitService


CONSENT_TEXT_VERSION = "offer_terms_v1"


class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.offer_limit_service = OfferLimitService()

    def create_offer(self, request: OfferCreateRequest) -> Offer | OfferLimitResult:
        if not request.consent_accepted:
            raise ValueError("Для отправки предложения нужно принять условия участия")

        if request.offer_type == OfferType.PHYSICAL_ITEM and not request.photo_urls:
            raise ValueError("Для физического предмета нужно добавить хотя бы одно фото")

        if len(request.photo_urls) > 3:
            raise ValueError("Можно добавить не больше 3 фото")

        user = self._get_or_create_user(request)

        total_user_offers = self._get_total_user_offers_count(user.id)
        today_user_offers = self._get_today_user_offers_count(user.id)
        last_offer_at = self._get_last_offer_created_at(user.id)

        limit_result = self.offer_limit_service.check_limit(
            user_created_at=user.created_at,
            total_user_offers=total_user_offers,
            today_user_offers=today_user_offers,
            last_offer_at=last_offer_at,
        )

        if not limit_result.allowed:
            return limit_result

        now = datetime.now(timezone.utc)

        offer = Offer(
            user_id=user.id,
            title=request.title,
            description=request.description,
            offer_type=request.offer_type.value,
            city=request.city,
            declared_value=request.declared_value,
            exchange_preference=request.exchange_preference.value,
            status=OfferStatus.NEW.value,
            is_public=False,
            participant_visible=request.participant_visible,
            participant_public_name=request.participant_public_name,
            consent_accepted=True,
            consent_accepted_at=now,
            consent_text_version=CONSENT_TEXT_VERSION,
            requires_contract=False,
            contract_status=ContractStatus.NOT_REQUIRED.value,
        )

        self.db.add(offer)
        self.db.flush()

        for photo_url in request.photo_urls:
            self.db.add(
                OfferPhoto(
                    offer_id=offer.id,
                    photo_url=photo_url,
                )
            )

        self.db.commit()
        self.db.refresh(offer)

        return offer

    def _get_or_create_user(self, request: OfferCreateRequest) -> User:
        messenger_account = self.db.scalar(
            select(MessengerAccount).where(
                MessengerAccount.messenger_type == request.messenger_type.value,
                MessengerAccount.external_user_id == request.external_user_id,
            )
        )

        if messenger_account is not None:
            user = self.db.get(User, messenger_account.user_id)

            if user is None:
                raise RuntimeError("MessengerAccount найден, но связанный User отсутствует")

            return user

        display_name = self._build_display_name(request)

        user = User(display_name=display_name)
        self.db.add(user)
        self.db.flush()

        messenger_account = MessengerAccount(
            user_id=user.id,
            messenger_type=request.messenger_type.value,
            external_user_id=request.external_user_id,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        self.db.add(messenger_account)
        self.db.flush()

        return user

    def _build_display_name(self, request: OfferCreateRequest) -> str | None:
        full_name_parts = [
            request.first_name,
            request.last_name,
        ]

        full_name = " ".join(part for part in full_name_parts if part)

        if full_name:
            return full_name

        if request.username:
            return request.username

        return None

    def _get_total_user_offers_count(self, user_id: UUID) -> int:
        return self.db.scalar(
            select(func.count(Offer.id)).where(Offer.user_id == user_id)
        ) or 0

    def _get_today_user_offers_count(self, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

        return self.db.scalar(
            select(func.count(Offer.id)).where(
                Offer.user_id == user_id,
                Offer.created_at >= today_start,
            )
        ) or 0

    def _get_last_offer_created_at(self, user_id: UUID) -> datetime | None:
        return self.db.scalar(
            select(Offer.created_at)
            .where(Offer.user_id == user_id)
            .order_by(Offer.created_at.desc())
            .limit(1)
        )