from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.db.models.deal import Deal
from app.db.models.item import Item
from app.db.models.offer import Offer
from app.db.models.user import User
from app.schemas.auth import (
    AccountResponse,
    AccountPasswordUpdateRequest,
    AccountPasswordUpdateResponse,
    AccountUpdateRequest,
    AuthUserResponse,
    LoginRequest,
    LoginResponse,
    MarketingConsentRequest,
    RegisterRequest,
    TelegramLoginStartResponse,
    TelegramLoginStatusResponse,
    UserConsentResponse,
)
from app.schemas.deal import UserDealListItem
from app.schemas.internal_telegram import TelegramLinkResponse
from app.schemas.offer import UserOfferListItem
from app.services.auth_service import AuthService
from app.services.user_identity_service import UserIdentityService


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def _auth_user_response(user: User, service: AuthService) -> AuthUserResponse:
    active_auth_account = next(
        (auth_account for auth_account in user.auth_accounts if auth_account.is_active),
        None,
    )

    return AuthUserResponse(
        id=user.id,
        display_name=user.display_name,
        login=active_auth_account.login if active_auth_account is not None else None,
        phone=user.phone,
        phone_verified=user.phone_verified,
        email=user.email,
        is_active=user.is_active,
        roles=service.get_user_roles(user),
    )


def _consent_response(consent) -> UserConsentResponse:
    return UserConsentResponse(
        document_code=consent.document_code,
        document_version=consent.document_version,
        status=consent.status,
        accepted_at=consent.accepted_at,
        revoked_at=consent.revoked_at,
        source=consent.source,
        consent_payload=consent.consent_payload,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user = service.authenticate(request.login, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    return LoginResponse(
        access_token=service.create_access_token(user),
        user=_auth_user_response(user, service),
    )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(
    registration_request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    try:
        user = service.register_user(
            registration_request,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        access_token=service.create_access_token(user),
        user=_auth_user_response(user, service),
    )


@router.post("/telegram/login-link", response_model=TelegramLoginStartResponse)
def create_telegram_login_link(
    db: Session = Depends(get_db),
):
    result = UserIdentityService(db).create_telegram_login_link()

    return TelegramLoginStartResponse(
        request_id=result.request_id,
        deep_link=result.deep_link or None,
        expires_at=result.expires_at,
    )


@router.get("/telegram/login-link/{request_id}", response_model=TelegramLoginStatusResponse)
def telegram_login_status(
    request_id: UUID,
    db: Session = Depends(get_db),
):
    identity_service = UserIdentityService(db)
    result = identity_service.get_telegram_login_status(request_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram login request not found",
        )

    if result.status != "authenticated" or result.user is None:
        return TelegramLoginStatusResponse(status=result.status)

    auth_service = AuthService(db)
    return TelegramLoginStatusResponse(
        status="authenticated",
        access_token=auth_service.create_access_token(result.user),
        user=_auth_user_response(result.user, auth_service),
    )


@router.get("/me", response_model=AuthUserResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _auth_user_response(current_user, AuthService(db))


@router.get("/account", response_model=AccountResponse)
def account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user_response = _auth_user_response(current_user, service).model_dump()

    return AccountResponse(
        **user_response,
        created_at=current_user.created_at,
        consents=[_consent_response(consent) for consent in current_user.consents],
    )


@router.patch("/account", response_model=AccountResponse)
def update_account(
    request: AccountUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    try:
        current_user.display_name = request.display_name.strip()
        current_user.phone = service.normalize_phone(request.phone)
        current_user.phone_verified = False
        current_user.email = service.validate_email(request.email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    db.commit()
    db.refresh(current_user)
    user_response = _auth_user_response(current_user, service).model_dump()

    return AccountResponse(
        **user_response,
        created_at=current_user.created_at,
        consents=[_consent_response(consent) for consent in current_user.consents],
    )


@router.patch("/account/password", response_model=AccountPasswordUpdateResponse)
def update_account_password(
    request: AccountPasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    try:
        service.change_password(
            current_user,
            current_password=request.current_password,
            new_password=request.new_password,
            new_password_confirmation=request.new_password_confirmation,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AccountPasswordUpdateResponse()


@router.get("/account/telegram", response_model=TelegramLinkResponse)
def telegram_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    identity = UserIdentityService(db).get_user_telegram_identity(current_user.id)

    return TelegramLinkResponse(
        status="connected" if identity is not None else "not_connected",
        telegram_connected=identity is not None,
        telegram_username=identity.username if identity is not None else None,
    )


@router.post("/account/telegram/link", response_model=TelegramLinkResponse)
def create_telegram_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = UserIdentityService(db).create_telegram_link(current_user)
    return TelegramLinkResponse(
        status=result["status"],
        telegram_connected=result["status"] == "connected",
        telegram_username=result["telegram_username"] or None,
        deep_link=result["deep_link"] or None,
    )


@router.get("/me/offers", response_model=list[UserOfferListItem])
def my_offers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(Offer.user_id == current_user.id)
        .order_by(Offer.created_at.desc())
    )

    return db.scalars(query).all()


@router.get("/me/deals", response_model=list[UserDealListItem])
def my_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned_item_ids = select(Item.id).where(Item.user_id == current_user.id)
    owned_offer_ids = select(Offer.id).where(Offer.user_id == current_user.id)

    query = (
        select(Deal)
        .where(
            or_(
                Deal.given_item_id.in_(owned_item_ids),
                Deal.received_item_id.in_(owned_item_ids),
                Deal.offer_id.in_(owned_offer_ids),
                Deal.participant_user_id == current_user.id,
            )
        )
        .order_by(Deal.created_at.desc())
    )

    user_deals = []

    for deal in db.scalars(query).all():
        offer = db.get(Offer, deal.offer_id) if deal.offer_id is not None else None
        given_item = db.get(Item, deal.given_item_id)
        received_item = db.get(Item, deal.received_item_id)
        item = received_item if received_item is not None and received_item.user_id == current_user.id else given_item

        if item is None:
            continue

        user_deals.append(
            UserDealListItem(
                id=deal.id,
                status=deal.status,
                status_label=deal.status_label,
                offer_id=deal.offer_id,
                offer_title=offer.title if offer is not None else None,
                item_id=item.id,
                item_title=item.title,
                created_at=deal.created_at,
            )
        )

    return user_deals


@router.patch("/me/consents/marketing", response_model=UserConsentResponse)
def update_marketing_consent(
    request: MarketingConsentRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    try:
        consent = service.update_marketing_consent(
            current_user,
            request,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _consent_response(consent)
