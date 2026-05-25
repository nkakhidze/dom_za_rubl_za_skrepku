import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ItemType(str, Enum):
    PHYSICAL_ITEM = "physical_item"
    SERVICE = "service"
    MONEY = "money"


class OwnerType(str, Enum):
    PERSONAL = "personal"
    TOM_SAWYER_FEST = "tom_sawyer_fest"
    PARTNER_ORG = "partner_org"
    OTHER = "other"


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    item_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Важно: это НЕ отдаём в public API.
    # Нужно только для админки.
    internal_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valuation_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OwnerType.PERSONAL.value,
    )

    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    public_story: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

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