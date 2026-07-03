from collections.abc import Generator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.db.models.item import Item, ItemStatus, ItemType, OwnerType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.telegram_notification_event import TelegramNotificationEvent
from app.db.models.user import User
from app.db.models.user_identity import IdentityProvider, UserIdentity
from app.main import app
from app.services.auth_service import AuthService
from app.services.offer_moderation_service import OfferModerationService
from app.services.telegram_notification_service import TelegramNotificationEventService


INTERNAL_TOKEN = "test-telegram-internal-token"


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(engine)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "public_base_url", "http://testserver")
    monkeypatch.setattr(settings, "telegram_internal_api_token", INTERNAL_TOKEN)
    monkeypatch.setattr(settings, "telegram_bot_username", "paperclip_test_bot")

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def internal_headers(token: str = INTERNAL_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def png_bytes() -> bytes:
    image = BytesIO()
    Image.new("RGB", (32, 32), (30, 140, 90)).save(image, format="PNG")
    return image.getvalue()


def resolve_telegram_user(client: TestClient, telegram_user_id: str = "tg-1") -> dict:
    response = client.post(
        "/api/internal/telegram/users/resolve",
        headers=internal_headers(),
        json={
            "telegram_user_id": telegram_user_id,
            "username": "first_username",
            "first_name": "Иван",
            "last_name": "Иванов",
            "language_code": "ru",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_internal_telegram_auth_is_required(client: TestClient):
    response = client.post(
        "/api/internal/telegram/users/resolve",
        json={"telegram_user_id": "tg-1"},
    )
    assert response.status_code == 401

    response = client.post(
        "/api/internal/telegram/users/resolve",
        headers=internal_headers("wrong"),
        json={"telegram_user_id": "tg-1"},
    )
    assert response.status_code == 403

    response = client.post(
        "/api/internal/telegram/users/resolve",
        headers=internal_headers(),
        json={"telegram_user_id": "tg-1"},
    )
    assert response.status_code == 200


def test_resolve_creates_user_identity_once_and_updates_username(client: TestClient):
    first = resolve_telegram_user(client, "tg-identity")
    assert first["created"] is True

    second_response = client.post(
        "/api/internal/telegram/users/resolve",
        headers=internal_headers(),
        json={
            "telegram_user_id": "tg-identity",
            "username": "updated_username",
            "first_name": "Иван",
        },
    )
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["created"] is False
    assert second["user_id"] == first["user_id"]

    with next(app.dependency_overrides[get_db]()) as db:
        identities = db.scalars(select(UserIdentity)).all()
        assert len(identities) == 1
        assert identities[0].username == "updated_username"


def test_internal_offer_creation_is_idempotent_and_saves_photos(client: TestClient):
    response = client.post(
        "/api/internal/telegram/offers",
        headers=internal_headers(),
        data={
            "telegram_user_id": "tg-offer",
            "username": "offer_user",
            "title": "Кружка",
            "description": "Керамическая кружка в хорошем состоянии.",
            "city": "Томск",
            "declared_value": "500",
            "participant_public_name": "Иван",
            "participant_visible": "true",
            "idempotency_key": "telegram:tg-offer:same-key",
        },
        files=[("photos", ("mug.png", png_bytes(), "image/png"))],
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == OfferStatus.NEW.value

    duplicate_response = client.post(
        "/api/internal/telegram/offers",
        headers=internal_headers(),
        data={
            "telegram_user_id": "tg-offer",
            "title": "Кружка дубль",
            "description": "Повторный запрос не должен создать новый оффер.",
            "idempotency_key": "telegram:tg-offer:same-key",
        },
        files=[("photos", ("mug.png", png_bytes(), "image/png"))],
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["offer_id"] == created["offer_id"]

    with next(app.dependency_overrides[get_db]()) as db:
        offers = db.scalars(select(Offer)).all()
        assert len(offers) == 1
        assert offers[0].photos
        assert offers[0].photos[0].thumbnail_url
        assert offers[0].user.phone is None


def test_account_link_merges_telegram_user_offers_into_site_user(client: TestClient):
    telegram_offer = client.post(
        "/api/internal/telegram/offers",
        headers=internal_headers(),
        data={
            "telegram_user_id": "tg-link",
            "title": "Telegram предмет",
            "description": "Предложение, созданное до связывания аккаунтов.",
            "idempotency_key": "telegram:tg-link:offer",
        },
        files=[("photos", ("item.png", png_bytes(), "image/png"))],
    )
    assert telegram_offer.status_code == 201

    with next(app.dependency_overrides[get_db]()) as db:
        site_user = AuthService(db).create_auth_user("site-user", "password", "Site User")
        site_token = AuthService(db).create_access_token(site_user)

    link_response = client.post(
        "/api/auth/account/telegram/link",
        headers={"Authorization": f"Bearer {site_token}"},
    )
    assert link_response.status_code == 200
    deep_link = link_response.json()["deep_link"]
    raw_token = deep_link.rsplit("link_", 1)[1]
    assert raw_token

    consume_response = client.post(
        "/api/internal/telegram/account-links/consume",
        headers=internal_headers(),
        json={
            "token": raw_token,
            "telegram_user_id": "tg-link",
            "username": "linked_user",
        },
    )
    assert consume_response.status_code == 200
    assert consume_response.json()["merged_user_id"] is not None

    my_offers_response = client.get(
        "/api/auth/me/offers",
        headers={"Authorization": f"Bearer {site_token}"},
    )
    assert my_offers_response.status_code == 200
    assert [offer["title"] for offer in my_offers_response.json()] == ["Telegram предмет"]

    with next(app.dependency_overrides[get_db]()) as db:
        inactive_users = db.scalars(
            select(User).where(User.merged_into_user_id.is_not(None))
        ).all()
        assert len(inactive_users) == 1
        identity = db.scalar(
            select(UserIdentity).where(
                UserIdentity.provider == IdentityProvider.TELEGRAM.value,
                UserIdentity.provider_user_id == "tg-link",
            )
        )
        assert str(identity.user_id) == consume_response.json()["user_id"]


def test_telegram_login_link_allows_site_login_after_bot_confirmation(client: TestClient):
    login_link_response = client.post("/api/auth/telegram/login-link")
    assert login_link_response.status_code == 200
    login_link = login_link_response.json()
    assert login_link["status"] == "pending"
    assert "login_" in login_link["deep_link"]

    pending_response = client.get(f"/api/auth/telegram/login-link/{login_link['request_id']}")
    assert pending_response.status_code == 200
    assert pending_response.json()["status"] == "pending"
    assert pending_response.json()["access_token"] is None

    raw_token = login_link["deep_link"].rsplit("login_", 1)[1]
    consume_response = client.post(
        "/api/internal/telegram/login-links/consume",
        headers=internal_headers(),
        json={
            "token": raw_token,
            "telegram_user_id": "tg-site-login",
            "username": "site_login_user",
            "first_name": "Site",
            "last_name": "Login",
        },
    )
    assert consume_response.status_code == 200

    authenticated_response = client.get(
        f"/api/auth/telegram/login-link/{login_link['request_id']}"
    )
    assert authenticated_response.status_code == 200
    authenticated = authenticated_response.json()
    assert authenticated["status"] == "authenticated"
    assert authenticated["access_token"]
    assert authenticated["user"]["display_name"] == "Site Login"

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {authenticated['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["id"] == authenticated["user"]["id"]


def test_chain_selection_notification_is_persisted_and_not_duplicated(client: TestClient):
    resolve_telegram_user(client, "tg-selected")

    offer_response = client.post(
        "/api/internal/telegram/offers",
        headers=internal_headers(),
        data={
            "telegram_user_id": "tg-selected",
            "title": "Следующий предмет",
            "description": "Предмет для включения в цепочку обменов.",
            "idempotency_key": "telegram:tg-selected:offer",
        },
        files=[("photos", ("item.png", png_bytes(), "image/png"))],
    )
    assert offer_response.status_code == 201

    class FakeNotificationService:
        def __init__(self) -> None:
            self.messages: list[tuple[str, str]] = []

        def send_telegram_message(self, telegram_id: str, text: str) -> bool:
            self.messages.append((telegram_id, text))
            return True

    fake_notifications = FakeNotificationService()

    with next(app.dependency_overrides[get_db]()) as db:
        current_item = Item(
            title="Скрепка",
            description="Стартовый предмет",
            item_type=ItemType.PHYSICAL_ITEM.value,
            owner_type=OwnerType.TOM_SAWYER_FEST.value,
            status=ItemStatus.CURRENT.value,
            sequence_number=1,
            is_current=True,
            is_public=True,
        )
        db.add(current_item)
        db.commit()

        deal = OfferModerationService(
            db,
            notification_service=fake_notifications,
        ).select_next_offer(offer_response.json()["offer_id"])

        TelegramNotificationEventService(
            db,
            notification_service=fake_notifications,
        ).send_chain_item_selected_once(
            user_id=deal.participant_user_id,
            entity_id=deal.offer_id,
        )

        events = db.scalars(select(TelegramNotificationEvent)).all()
        assert len(events) == 1

    assert len(fake_notifications.messages) == 1
    assert fake_notifications.messages[0][0] == "tg-selected"
    assert "Ваш предмет включён в цепочку обмена" in fake_notifications.messages[0][1]
