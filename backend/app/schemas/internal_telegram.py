from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TelegramResolveUserRequest(BaseModel):
    telegram_user_id: str = Field(min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    language_code: str | None = Field(default=None, max_length=20)


class TelegramResolveUserResponse(BaseModel):
    user_id: UUID
    created: bool
    telegram_connected: bool = True


class TelegramOfferCreateResponse(BaseModel):
    offer_id: UUID
    status: str
    status_label: str
    created_at: datetime


class TelegramOfferListItem(BaseModel):
    id: UUID
    title: str
    status: str
    status_label: str
    created_at: datetime
    thumbnail_urls: list[str] = []


class TelegramConsumeLinkRequest(BaseModel):
    token: str = Field(min_length=16)
    telegram_user_id: str = Field(min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    language_code: str | None = Field(default=None, max_length=20)


class TelegramConsumeLinkResponse(BaseModel):
    user_id: UUID
    telegram_connected: bool = True
    merged_user_id: UUID | None = None
    already_linked: bool = False


class TelegramLinkResponse(BaseModel):
    status: str
    telegram_connected: bool
    telegram_username: str | None = None
    deep_link: str | None = None
