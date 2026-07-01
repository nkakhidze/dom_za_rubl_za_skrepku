import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class ItemStatus(str, Enum):
    CURRENT = "current"
    PAST = "past"
    FINAL = "final"
    PLANNED = "planned"
    # Legacy statuses used by the old response-item flow.
    ACTIVE = "active"
    ARCHIVED = "archived"


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    source_offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id"),
        nullable=True,
    )

    user: Mapped["User | None"] = relationship(back_populates="items")

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

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ItemStatus.CURRENT.value,
    )
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    public_story: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    vk_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    dzen_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    rutube_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    photos: Mapped[list["ItemPhoto"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ItemPhoto.sort_order",
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
    def photo_urls(self) -> list[str]:
        urls = [photo.photo_url for photo in self.photos]

        if not urls and self.photo_url:
            urls.append(self.photo_url)

        return urls

    @property
    def thumbnail_urls(self) -> list[str]:
        urls = [photo.thumbnail_url or photo.photo_url for photo in self.photos]

        if not urls and self.photo_url:
            urls.append(self.photo_url)

        return urls
