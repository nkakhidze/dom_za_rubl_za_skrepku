import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id"),
        nullable=True,
    )

    step_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    given_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id"),
        nullable=False,
    )

    received_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
    )

    participant_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    participant_public_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    public_story: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    deal_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

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

    @property
    def status_label(self) -> str:
        return DEAL_STATUS_LABELS.get(self.status, self.status)

    @property
    def item_id(self) -> uuid.UUID:
        return self.given_item_id


class DealStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    # Legacy marketplace response statuses.
    NEW = "new"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


DEAL_STATUS_LABELS = {
    DealStatus.PLANNED.value: "Запланирована",
    DealStatus.COMPLETED.value: "Завершена",
    DealStatus.CANCELLED.value: "Отменена",
    DealStatus.NEW.value: "Новая заявка",
    DealStatus.ACCEPTED.value: "Принята",
    DealStatus.REJECTED.value: "Отклонена",
}
