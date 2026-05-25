from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.messenger_account import MessengerType
from app.db.models.offer import ExchangePreference, OfferType


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