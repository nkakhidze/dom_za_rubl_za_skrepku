from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.deal import DealStatus
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
    offer_id: UUID | None
    step_number: int

    given_item_id: UUID
    received_item_id: UUID
    item_id: UUID | None = None
    status: str
    status_label: str

    participant_user_id: UUID | None
    participant_public_name: str | None
    participant_visible: bool

    public_story: str | None
    video_url: str | None
    is_public: bool

    deal_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicExchangeChainDealItem(BaseModel):
    id: UUID
    title: str
    description: str | None
    public_story: str | None = None
    photo_url: str | None
    photo_urls: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    thumbnail_urls: list[str] = Field(default_factory=list)


class PublicExchangeChainItem(BaseModel):
    id: UUID
    step_number: int
    status: str

    given_item: PublicExchangeChainDealItem
    received_item: PublicExchangeChainDealItem

    public_story: str | None
    video_url: str | None

    participant_public_name: str | None
    participant_visible: bool

    deal_date: datetime


class AdminDealCreateFromOfferRequest(BaseModel):
    given_item_id: UUID

    owner_type: OwnerType = OwnerType.PERSONAL
    owner_name: str | None = Field(default=None, max_length=255)

    public_story: str | None = None
    video_url: str | None = Field(default=None, max_length=1000)
    photo_url: str | None = Field(default=None, max_length=1000)

    is_public: bool = False


class DealCreateRequest(BaseModel):
    offer_id: UUID
    item_id: UUID


class DealCreateResponse(BaseModel):
    id: UUID
    offer_id: UUID
    item_id: UUID
    status: str
    status_label: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserDealListItem(BaseModel):
    id: UUID
    status: str
    status_label: str
    offer_id: UUID | None
    offer_title: str | None
    item_id: UUID
    item_title: str
    created_at: datetime


class AdminDealStatusUpdateRequest(BaseModel):
    status: DealStatus


class AdminDealMessengerAccountResponse(BaseModel):
    messenger_type: str
    external_user_id: str
    username: str | None
    first_name: str | None
    last_name: str | None

    class Config:
        from_attributes = True


class AdminDealUserResponse(BaseModel):
    id: UUID
    display_name: str | None
    phone: str | None
    messenger_accounts: list[AdminDealMessengerAccountResponse]

    class Config:
        from_attributes = True


class AdminDealListItem(BaseModel):
    deal_id: UUID
    deal_status: str
    deal_status_label: str
    deal_created_at: datetime
    offer_id: UUID | None
    offer_title: str | None
    offer_status: str | None
    offer_is_public: bool | None
    offer_owner_user_id: UUID | None
    offer_owner_display_name: str | None
    item_id: UUID
    item_title: str
    item_status: str
    item_owner_user_id: UUID | None
    item_owner_display_name: str | None


class AdminDealOfferDetail(BaseModel):
    id: UUID
    title: str
    description: str
    city: str | None
    public_value: int | None
    status: str
    is_public: bool
    photo_urls: list[str]


class AdminDealItemDetail(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str


class AdminDealDetail(BaseModel):
    id: UUID
    status: str
    status_label: str
    created_at: datetime
    updated_at: datetime
    offer: AdminDealOfferDetail | None
    item: AdminDealItemDetail
    offer_owner: AdminDealUserResponse | None
    item_owner: AdminDealUserResponse | None
