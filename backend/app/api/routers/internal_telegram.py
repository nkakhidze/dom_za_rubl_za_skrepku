from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_telegram_internal_access
from app.db.models.messenger_account import MessengerType
from app.db.models.offer import ExchangePreference, Offer, OfferType
from app.schemas.internal_telegram import (
    TelegramConsumeLinkRequest,
    TelegramConsumeLinkResponse,
    TelegramOfferCreateResponse,
    TelegramOfferListItem,
    TelegramPhoneUpdateRequest,
    TelegramResolveUserRequest,
    TelegramResolveUserResponse,
)
from app.schemas.offer import OfferCreateRequest
from app.services.file_storage_service import FileStorageService
from app.services.image_service import ImageUploadError, delete_uploaded_image_files
from app.services.offer_limit_service import OfferLimitResult
from app.services.offer_service import OfferService
from app.services.auth_service import AuthService
from app.services.user_identity_service import (
    AccountLinkConflictError,
    AccountLinkError,
    TelegramUserPayload,
    UserIdentityService,
)


router = APIRouter(
    prefix="/internal/telegram",
    tags=["internal telegram"],
    dependencies=[Depends(require_telegram_internal_access)],
)


def _payload_from_request(
    request: TelegramResolveUserRequest | TelegramConsumeLinkRequest,
) -> TelegramUserPayload:
    return TelegramUserPayload(
        telegram_user_id=request.telegram_user_id,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        language_code=request.language_code,
    )


@router.post("/users/resolve", response_model=TelegramResolveUserResponse)
def resolve_user(
    request: TelegramResolveUserRequest,
    db: Session = Depends(get_db),
):
    result = UserIdentityService(db).resolve_telegram_user(_payload_from_request(request))
    return TelegramResolveUserResponse(
        user_id=result.user.id,
        created=result.created,
        telegram_phone=result.user.telegram_phone,
    )


@router.post("/users/phone", response_model=TelegramResolveUserResponse)
def update_telegram_phone(
    request: TelegramPhoneUpdateRequest,
    db: Session = Depends(get_db),
):
    phone = AuthService.normalize_phone(request.phone)
    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone is required",
        )

    result = UserIdentityService(db).resolve_telegram_user(
        _payload_from_request(request),
        commit=False,
    )
    result.user.telegram_phone = phone
    db.commit()
    db.refresh(result.user)

    return TelegramResolveUserResponse(
        user_id=result.user.id,
        created=result.created,
        telegram_phone=result.user.telegram_phone,
    )


@router.get("/offers", response_model=list[TelegramOfferListItem])
def get_my_offers(
    telegram_user_id: str,
    db: Session = Depends(get_db),
):
    identity_result = UserIdentityService(db).resolve_telegram_user(
        TelegramUserPayload(telegram_user_id=telegram_user_id),
    )
    query = (
        select(Offer)
        .options(selectinload(Offer.photos))
        .where(Offer.user_id == identity_result.user.id)
        .order_by(Offer.created_at.desc())
        .limit(10)
    )
    return db.scalars(query).all()


@router.post("/account-links/consume", response_model=TelegramConsumeLinkResponse)
def consume_account_link(
    request: TelegramConsumeLinkRequest,
    db: Session = Depends(get_db),
):
    try:
        result = UserIdentityService(db).consume_telegram_link(
            request.token,
            _payload_from_request(request),
        )
    except AccountLinkConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AccountLinkError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc

    return TelegramConsumeLinkResponse(
        user_id=result.user.id,
        merged_user_id=result.merged_user_id,
        already_linked=result.already_linked,
    )


@router.post("/login-links/consume", response_model=TelegramConsumeLinkResponse)
def consume_login_link(
    request: TelegramConsumeLinkRequest,
    db: Session = Depends(get_db),
):
    try:
        result = UserIdentityService(db).consume_telegram_login_link(
            request.token,
            _payload_from_request(request),
        )
    except AccountLinkError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc

    return TelegramConsumeLinkResponse(
        user_id=result.user.id,
        merged_user_id=None,
        already_linked=False,
    )


@router.post(
    "/offers",
    response_model=TelegramOfferCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    telegram_user_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    idempotency_key: Annotated[str, Form()],
    username: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    language_code: Annotated[str | None, Form()] = None,
    city: Annotated[str | None, Form()] = None,
    declared_value: Annotated[int | None, Form()] = None,
    exchange_preference: Annotated[str, Form()] = ExchangePreference.ANY_OFFER.value,
    participant_public_name: Annotated[str | None, Form()] = None,
    participant_visible: Annotated[bool, Form()] = True,
    photos: Annotated[list[UploadFile], File()] = [],
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Offer).where(Offer.source_idempotency_key == idempotency_key)
    )
    if existing is not None:
        return TelegramOfferCreateResponse(
            offer_id=existing.id,
            status=existing.status,
            status_label=existing.status_label,
            created_at=existing.created_at,
        )

    identity_result = UserIdentityService(db).resolve_telegram_user(
        TelegramUserPayload(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        ),
        commit=False,
    )

    storage = FileStorageService()
    uploaded_images = []

    try:
        for photo in photos:
            uploaded_images.append(await storage.save_image(photo))
    except ImageUploadError as exc:
        delete_uploaded_image_files(
            *[image.photo_url for image in uploaded_images],
            *[image.thumbnail_url for image in uploaded_images],
        )
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    request = OfferCreateRequest(
        messenger_type=MessengerType.TELEGRAM,
        external_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        title=title,
        description=description,
        offer_type=OfferType.PHYSICAL_ITEM,
        city=city,
        declared_value=declared_value,
        photo_urls=[image.photo_url for image in uploaded_images],
        photo_thumbnail_urls=[image.thumbnail_url for image in uploaded_images],
        photo_widths=[image.width for image in uploaded_images],
        photo_heights=[image.height for image in uploaded_images],
        photo_thumbnail_widths=[image.thumbnail_width for image in uploaded_images],
        photo_thumbnail_heights=[image.thumbnail_height for image in uploaded_images],
        photo_size_bytes=[image.size_bytes for image in uploaded_images],
        photo_thumbnail_size_bytes=[image.thumbnail_size_bytes for image in uploaded_images],
        exchange_preference=ExchangePreference(exchange_preference),
        consent_accepted=True,
        participant_visible=participant_visible,
        participant_public_name=participant_public_name,
        source_idempotency_key=idempotency_key,
    )

    try:
        result = OfferService(db).create_offer(request, current_user=identity_result.user)
    except ValueError as exc:
        delete_uploaded_image_files(
            *[image.photo_url for image in uploaded_images],
            *[image.thumbnail_url for image in uploaded_images],
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if isinstance(result, OfferLimitResult):
        delete_uploaded_image_files(
            *[image.photo_url for image in uploaded_images],
            *[image.thumbnail_url for image in uploaded_images],
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=result.message)

    return TelegramOfferCreateResponse(
        offer_id=result.id,
        status=result.status,
        status_label=result.status_label,
        created_at=result.created_at,
    )
