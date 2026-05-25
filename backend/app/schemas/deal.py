from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.item import ItemType, OwnerType


class AdminDealCreateRequest(BaseModel):
    given_item_id: UUID

    received_item_title: str = Field(min_length=2, max_length=255)
    received_item_description: str | None = None
    received_item_type: ItemType

    # Не отдаём в public API. Только для админки.
    received_item_internal_value: int | None = Field(default=None, ge=0)
    received_item_valuation_source: str | None = None

    owner_type: OwnerType = OwnerType.PERSONAL
    owner_name: str | None = Field(default=None, max_length=255)

    participant_user_id: UUID | None = None
    participant_public_name: str | None = Field(default=None, max_length=255)
    participant_visible: bool = False

    public_story: str | None = None
    video_url: str | None = Field(default=None, max_length=1000)
    photo_url: str | None = Field(default=None, max_length=1000)

    is_public: bool = False


class AdminDealResponse(BaseModel):
    id: UUID
    step_number: int

    given_item_id: UUID
    received_item_id: UUID

    participant_user_id: UUID | None
    participant_public_name: str | None
    participant_visible: bool

    public_story: str | None
    video_url: str | None
    is_public: bool

    deal_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PublicExchangeChainItem(BaseModel):
    step_number: int

    given_item_title: str
    received_item_title: str

    public_story: str | None
    video_url: str | None

    participant_public_name: str | None
    participant_visible: bool

    deal_date: datetime