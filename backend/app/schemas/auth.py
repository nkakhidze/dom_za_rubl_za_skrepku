from uuid import UUID
from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class AuthUserResponse(BaseModel):
    id: UUID
    display_name: str | None
    login: str | None = None
    phone: str | None = None
    phone_verified: bool = False
    email: str | None = None
    is_active: bool
    roles: list[str]


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class RequiredConsentRequest(BaseModel):
    accepted: bool
    version: str = Field(min_length=1, max_length=50)


class MarketingConsentRequest(BaseModel):
    version: str = Field(
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("version", "document_version"),
    )
    email: bool = False
    telegram: bool = False
    max: bool = False


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    password_confirmation: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=6, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    is_adult_confirmed: bool
    user_agreement: RequiredConsentRequest
    personal_data_consent: RequiredConsentRequest
    privacy_policy_version: str = Field(min_length=1, max_length=50)
    marketing_consent: MarketingConsentRequest | None = None


class UserConsentResponse(BaseModel):
    document_code: str
    document_version: str
    status: str
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    source: str
    consent_payload: dict


class AccountResponse(AuthUserResponse):
    created_at: datetime
    consents: list[UserConsentResponse]


class AccountUpdateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)


class RoleUpdateRequest(BaseModel):
    role: str = Field(min_length=1, max_length=50)


class AdminUserListItem(BaseModel):
    id: UUID
    display_name: str | None
    phone: str | None
    phone_verified: bool
    is_active: bool
    roles: list[str]


class AdminUserDetail(AdminUserListItem):
    messenger_accounts: list[dict]
    auth_logins: list[str]


class PhoneUpdateRequest(BaseModel):
    phone: str = Field(min_length=3, max_length=50)
