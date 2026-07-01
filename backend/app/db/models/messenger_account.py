import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessengerType(str, Enum):
    TELEGRAM = "telegram"
    MAX = "max"
    WEB = "web"


class MessengerAccount(Base):
    __tablename__ = "messenger_accounts"

    __table_args__ = (
        UniqueConstraint(
            "messenger_type",
            "external_user_id",
            name="uq_messenger_accounts_type_external_id",
        ),
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

    user: Mapped["User"] = relationship(back_populates="messenger_accounts")

    messenger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
