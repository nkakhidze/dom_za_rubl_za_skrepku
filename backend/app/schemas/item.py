from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.item import ItemType, OwnerType


class ItemPlatformLinks(BaseModel):
    vk_url: str | None = Field(default=None, max_length=1000)
    tiktok_url: str | None = Field(default=None, max_length=1000)
    youtube_url: str | None = Field(default=None, max_length=1000)
    dzen_url: str | None = Field(default=None, max_length=1000)
    rutube_url: str | None = Field(default=None, max_length=1000)
    instagram_url: str | None = Field(default=None, max_length=1000)


class AdminItemCreateRequest(ItemPlatformLinks):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None

    item_type: ItemType

    internal_value: int | None = Field(default=None, ge=0)
    valuation_source: str | None = None

    owner_type: OwnerType = OwnerType.PERSONAL
    owner_name: str | None = Field(default=None, max_length=255)

    is_current: bool = False
    is_public: bool = True

    public_story: str | None = None
    photo_url: str | None = Field(default=None, max_length=1000)
    sequence_number: int | None = Field(default=None, ge=0)


class AdminItemUpdateRequest(ItemPlatformLinks):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None

    item_type: ItemType | None = None
    status: str | None = Field(default=None, max_length=50)

    internal_value: int | None = Field(default=None, ge=0)
    valuation_source: str | None = None

    owner_type: OwnerType | None = None
    owner_name: str | None = Field(default=None, max_length=255)

    is_current: bool | None = None
    is_public: bool | None = None

    public_story: str | None = None
    photo_url: str | None = Field(default=None, max_length=1000)
    sequence_number: int | None = Field(default=None, ge=0)


class AdminItemPhotoCreateRequest(BaseModel):
    photo_url: str = Field(max_length=1000)
    sort_order: int = Field(default=0, ge=0)


class AdminItemPhotoResponse(BaseModel):
    id: UUID
    item_id: UUID
    photo_url: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserItemCreateRequest(BaseModel):
    user_id: UUID
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2)


class AdminItemResponse(ItemPlatformLinks):
    id: UUID
    user_id: UUID | None
    source_offer_id: UUID | None

    title: str
    description: str | None
    item_type: str
    status: str

    internal_value: int | None
    valuation_source: str | None

    owner_type: str
    owner_name: str | None

    is_current: bool
    is_public: bool
    sequence_number: int | None

    public_story: str | None
    photo_url: str | None
    photo_urls: list[str] = Field(default_factory=list)
    photos: list[AdminItemPhotoResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicCurrentItemResponse(BaseModel):
    id: UUID

    title: str
    description: str | None
    item_type: str

    public_story: str | None
    photo_url: str | None

    class Config:
        from_attributes = True


class PublicItemDetailResponse(ItemPlatformLinks):
    id: UUID
    title: str
    description: str | None
    item_type: str
    public_story: str | None
    photo_url: str | None
    photo_urls: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
