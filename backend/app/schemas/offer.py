from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.messenger_account import MessengerType
from app.db.models.offer import ExchangePreference, OfferStatus, OfferType



class OfferCreateRequest(BaseModel):
    messenger_type: MessengerType
    external_user_id: str = Field(min_length=1, max_length=255)

    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)

    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)

    offer_type: OfferType
    city: str | None = Field(default=None, max_length=100)

    declared_value: int | None = Field(default=None, ge=0)
    photo_urls: list[str] = Field(default_factory=list, max_length=3)

    exchange_preference: ExchangePreference = ExchangePreference.ANY_OFFER

    consent_accepted: bool
    participant_visible: bool = False
    participant_public_name: str | None = Field(default=None, max_length=255)


class OfferCreateResponse(BaseModel):
    id: UUID
    status: str
    message: str


class OfferLimitResponse(BaseModel):
    status: str = "limit_reached"
    next_allowed_date: datetime | None = None
    message: str


class PublicOfferListItem(BaseModel):
    id: UUID

    title: str
    description: str
    offer_type: str
    city: str | None

    public_value: int | None
    public_comment: str | None

    photo_urls: list[str] = Field(default_factory=list)

    participant_public_name: str | None = Field(
        default=None,
        validation_alias="public_participant_name",
    )

    status_label: str
    created_at: datetime

    class Config:
        from_attributes = True


class PublicOfferDetail(PublicOfferListItem):
    pass


class UserOfferListItem(BaseModel):
    id: UUID

    title: str
    description: str
    offer_type: str
    city: str | None

    declared_value: int | None
    status: str
    status_label: str
    is_public: bool
    public_comment: str | None

    participant_visible: bool
    participant_public_name: str | None

    photo_urls: list[str] = Field(default_factory=list)

    created_at: datetime

    class Config:
        from_attributes = True


class AdminOfferListItem(BaseModel):
    id: UUID
    user_id: UUID

    title: str
    description: str
    offer_type: str
    city: str | None

    declared_value: int | None
    moderated_value: int | None
    public_value: int | None

    photo_urls: list[str] = []

    exchange_preference: str
    status: str
    status_label: str

    is_public: bool
    public_comment: str | None

    participant_visible: bool
    participant_public_name: str | None

    valuation_source: str | None
    moderation_comment: str | None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminOfferDetail(AdminOfferListItem):
    consent_accepted: bool
    consent_accepted_at: datetime | None
    consent_text_version: str | None

    requires_contract: bool
    contract_status: str
    contract_file_key: str | None


class AdminOfferStatusUpdateRequest(BaseModel):
    status: OfferStatus


class AdminOfferModerationUpdateRequest(BaseModel):
    moderated_value: int | None = Field(default=None, ge=0)
    public_value: int | None = Field(default=None, ge=0)
    valuation_source: str | None = None
    moderation_comment: str | None = None

    is_public: bool | None = None
    public_comment: str | None = None

    participant_visible: bool | None = None
    participant_public_name: str | None = Field(default=None, max_length=255)


class AdminOfferPhotoResponse(BaseModel):
    id: UUID
    offer_id: UUID
    photo_url: str
    created_at: datetime

    class Config:
        from_attributes = True
