import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, String, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OfferType(str, Enum):
    PHYSICAL_ITEM = "physical_item"
    SERVICE = "service"


class OfferStatus(str, Enum):
    NEW = "new"
    NEED_DETAILS = "need_details"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


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

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    offer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

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

    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    participant_public_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    consent_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_text_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    requires_contract: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contract_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ContractStatus.NOT_REQUIRED.value,
    )
    contract_file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)