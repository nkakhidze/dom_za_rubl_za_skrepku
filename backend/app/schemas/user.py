from uuid import UUID

from pydantic import BaseModel, Field


class TelegramUserCreateRequest(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)


class TelegramUserResponse(BaseModel):
    id: UUID
    telegram_id: str
    display_name: str | None
