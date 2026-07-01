import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OfferType(str, Enum):
    PHYSICAL_ITEM = "physical_item"
    SERVICE = "service"


class OfferStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    SELECTED = "selected"
    HIDDEN = "hidden"
    REJECTED = "rejected"
    # Legacy marketplace statuses. Keep them readable while data is migrated.
    MODERATION = "moderation"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class OfferVisibilityStatus(str, Enum):
    NORMAL = "normal"
    LOW_PRIORITY = "low_priority"
    HIDDEN = "hidden"


OFFER_STATUS_LABELS = {
    OfferStatus.NEW.value: "Новая заявка",
    OfferStatus.REVIEWED.value: "Просмотрена",
    OfferStatus.SELECTED.value: "Выбрана в цепочку",
    OfferStatus.HIDDEN.value: "Скрыта",
    OfferStatus.REJECTED.value: "Отклонена",
    OfferStatus.MODERATION.value: "На модерации",
    OfferStatus.APPROVED.value: "Одобрено",
    OfferStatus.PUBLISHED.value: "Опубликовано",
    OfferStatus.ARCHIVED.value: "Снято с публикации",
}


class ExchangePreference(str, Enum):
    ANY_OFFER = "any_offer"
    COMPARABLE_VALUE_ONLY = "comparable_value_only"


class ContractStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    PREPARED = "prepared"
    SIGNED = "signed"


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("source_idempotency_key", name="uq_offers_source_idempotency_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="offers")

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    offer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Оценки НЕ показываем публично.
    # Они нужны только для админки и внутренней модерации.
    declared_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    moderated_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    public_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    valuation_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderation_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    exchange_preference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ExchangePreference.ANY_OFFER.value,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OfferStatus.NEW.value,
    )
    visibility_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OfferVisibilityStatus.NORMAL.value,
    )
    sort_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Legacy public offer fields. The sequential chain uses deals/items instead.
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    participant_public_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    consent_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    consent_text_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    requires_contract: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    contract_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ContractStatus.NOT_REQUIRED.value,
    )

    contract_file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    photos: Mapped[list["OfferPhoto"]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def photo_urls(self) -> list[str]:
        return [photo.photo_url for photo in self.photos]

    @property
    def thumbnail_urls(self) -> list[str]:
        return [photo.thumbnail_url or photo.photo_url for photo in self.photos]

    @property
    def public_participant_name(self) -> str | None:
        if not self.participant_visible:
            return None

        return self.participant_public_name

    @property
    def status_label(self) -> str:
        return OFFER_STATUS_LABELS.get(self.status, self.status)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
