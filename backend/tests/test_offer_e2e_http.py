from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.main import app


TEST_ADMIN_TOKEN = "test_admin_token"
ADMIN_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}


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
    )

    Base.metadata.create_all(engine)

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    monkeypatch.setattr(settings, "public_base_url", "http://testserver")
    monkeypatch.setattr(settings, "admin_api_token", TEST_ADMIN_TOKEN)

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


def upload_test_image(client: TestClient) -> str:
    response = client.post(
        "/api/files/images",
        files={
            "file": (
                "offer.png",
                b"\x89PNG\r\n\x1a\nfake-test-image",
                "image/png",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["photo_url"]
    assert payload["filename"].endswith(".png")

    return payload["photo_url"]


def assert_forbidden_public_fields_are_absent(payload: dict) -> None:
    forbidden_fields = {
        "user_id",
        "declared_value",
        "moderated_value",
        "moderation_comment",
        "status",
        "consent_accepted",
        "consent_accepted_at",
        "consent_text_version",
        "requires_contract",
        "contract_status",
        "contract_file_key",
    }

    assert forbidden_fields.isdisjoint(payload)


def test_offer_full_http_e2e(client: TestClient):
    photo_url = upload_test_image(client)

    create_response = client.post(
        "/api/offers",
        json={
            "messenger_type": "telegram",
            "external_user_id": "telegram-user-1",
            "username": "paperclip_user",
            "first_name": "Paperclip",
            "last_name": "Participant",
            "title": "Restoration tool set",
            "description": "A useful physical item for the next exchange step.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 3500,
            "photo_urls": [photo_url],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": True,
            "participant_public_name": "Public Participant",
        },
    )

    assert create_response.status_code == 201
    created_offer = create_response.json()
    offer_id = created_offer["id"]
    assert offer_id
    assert created_offer["status"] == "new"

    admin_list_response = client.get("/api/admin/offers", headers=ADMIN_HEADERS)
    assert admin_list_response.status_code == 200
    admin_offers = admin_list_response.json()
    admin_offer = next(offer for offer in admin_offers if offer["id"] == offer_id)
    assert admin_offer["photo_urls"] == [photo_url]

    admin_detail_response = client.get(
        f"/api/admin/offers/{offer_id}",
        headers=ADMIN_HEADERS,
    )
    assert admin_detail_response.status_code == 200
    admin_detail = admin_detail_response.json()
    assert admin_detail["id"] == offer_id
    user_id = admin_detail["user_id"]
    assert admin_detail["title"] == "Restoration tool set"
    assert admin_detail["photo_urls"] == [photo_url]
    assert "moderated_value" in admin_detail
    assert "moderation_comment" in admin_detail
    assert "user_id" in admin_detail

    user_offers_response = client.get(f"/api/users/{user_id}/offers")
    assert user_offers_response.status_code == 200
    user_offers = user_offers_response.json()
    user_offer = next(offer for offer in user_offers if offer["id"] == offer_id)
    assert user_offer["photo_urls"] == [photo_url]
    assert user_offer["status"] == "new"
    assert user_offer["is_public"] is False
    assert "moderation_comment" not in user_offer
    assert "valuation_source" not in user_offer
    assert "user_id" not in user_offer

    photos_response = client.get(
        f"/api/admin/offers/{offer_id}/photos",
        headers=ADMIN_HEADERS,
    )
    assert photos_response.status_code == 200
    photos = photos_response.json()
    assert len(photos) == 1
    assert photos[0]["photo_url"] == photo_url

    hidden_public_response = client.get(f"/api/offers/{offer_id}")
    assert hidden_public_response.status_code == 404

    moderation_response = client.patch(
        f"/api/admin/offers/{offer_id}/moderation",
        headers=ADMIN_HEADERS,
        json={
            "moderated_value": 3200,
            "public_value": 3000,
            "valuation_source": "Checked against similar listings.",
            "moderation_comment": "Internal moderation note.",
            "is_public": True,
            "public_comment": "A practical item for the exchange chain.",
            "participant_visible": True,
            "participant_public_name": "Published Participant",
        },
    )

    assert moderation_response.status_code == 200
    moderated_offer = moderation_response.json()
    assert moderated_offer["moderated_value"] == 3200
    assert moderated_offer["public_value"] == 3000
    assert moderated_offer["valuation_source"] == "Checked against similar listings."
    assert moderated_offer["moderation_comment"] == "Internal moderation note."
    assert moderated_offer["is_public"] is True
    assert moderated_offer["status"] == "published"
    assert moderated_offer["status_label"] == "Опубликовано"
    assert moderated_offer["public_comment"] == "A practical item for the exchange chain."
    assert moderated_offer["participant_visible"] is True
    assert moderated_offer["participant_public_name"] == "Published Participant"

    status_response = client.patch(
        f"/api/admin/offers/{offer_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "published"
    assert status_response.json()["is_public"] is True

    updated_user_offers_response = client.get(f"/api/users/{user_id}/offers")
    assert updated_user_offers_response.status_code == 200
    updated_user_offer = next(
        offer
        for offer in updated_user_offers_response.json()
        if offer["id"] == offer_id
    )
    assert updated_user_offer["status"] == "published"
    assert updated_user_offer["status_label"] == "Опубликовано"
    assert updated_user_offer["is_public"] is True
    assert updated_user_offer["photo_urls"] == [photo_url]

    public_list_response = client.get("/api/offers")
    assert public_list_response.status_code == 200
    public_offers = public_list_response.json()
    public_offer = next(offer for offer in public_offers if offer["id"] == offer_id)
    assert public_offer["title"] == "Restoration tool set"
    assert public_offer["photo_urls"] == [photo_url]
    assert public_offer["public_value"] == 3000
    assert public_offer["public_comment"] == "A practical item for the exchange chain."
    assert public_offer["participant_public_name"] == "Published Participant"
    assert_forbidden_public_fields_are_absent(public_offer)

    public_detail_response = client.get(f"/api/offers/{offer_id}")
    assert public_detail_response.status_code == 200
    public_detail = public_detail_response.json()
    assert public_detail["id"] == offer_id
    assert public_detail["title"] == "Restoration tool set"
    assert public_detail["photo_urls"] == [photo_url]
    assert public_detail["public_value"] == 3000
    assert public_detail["participant_public_name"] == "Published Participant"
    assert_forbidden_public_fields_are_absent(public_detail)


def test_public_http_endpoints_hide_participant_name_when_not_visible(
    client: TestClient,
):
    photo_url = upload_test_image(client)

    create_response = client.post(
        "/api/offers",
        json={
            "messenger_type": "telegram",
            "external_user_id": "telegram-user-private",
            "username": "private_user",
            "first_name": "Private",
            "last_name": "Participant",
            "title": "Private participant offer",
            "description": "A useful physical item with a hidden participant name.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 1500,
            "photo_urls": [photo_url],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": False,
            "participant_public_name": "Hidden Participant",
        },
    )
    assert create_response.status_code == 201
    offer_id = create_response.json()["id"]

    moderation_response = client.patch(
        f"/api/admin/offers/{offer_id}/moderation",
        headers=ADMIN_HEADERS,
        json={
            "is_public": True,
            "participant_visible": False,
            "participant_public_name": "Hidden Participant",
        },
    )
    assert moderation_response.status_code == 200

    public_list_response = client.get("/api/offers")
    assert public_list_response.status_code == 200
    public_offer = next(
        offer for offer in public_list_response.json() if offer["id"] == offer_id
    )
    assert public_offer["participant_public_name"] is None
    assert "participant_visible" not in public_offer

    public_detail_response = client.get(f"/api/offers/{offer_id}")
    assert public_detail_response.status_code == 200
    public_detail = public_detail_response.json()
    assert public_detail["participant_public_name"] is None
    assert "participant_visible" not in public_detail


def test_admin_offers_require_valid_admin_token(client: TestClient):
    missing_token_response = client.get("/api/admin/offers")
    assert missing_token_response.status_code == 401

    invalid_token_response = client.get(
        "/api/admin/offers",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert invalid_token_response.status_code == 401

    valid_token_response = client.get("/api/admin/offers", headers=ADMIN_HEADERS)
    assert valid_token_response.status_code == 200


def test_admin_moderation_requires_valid_admin_token(client: TestClient):
    photo_url = upload_test_image(client)

    create_response = client.post(
        "/api/offers",
        json={
            "messenger_type": "telegram",
            "external_user_id": "telegram-user-admin-auth",
            "username": "admin_auth_user",
            "first_name": "Admin",
            "last_name": "Auth",
            "title": "Admin auth offer",
            "description": "A useful physical item for admin auth testing.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 2100,
            "photo_urls": [photo_url],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": True,
            "participant_public_name": "Admin Auth Participant",
        },
    )
    assert create_response.status_code == 201
    offer_id = create_response.json()["id"]

    missing_token_response = client.patch(
        f"/api/admin/offers/{offer_id}/moderation",
        json={"is_public": True},
    )
    assert missing_token_response.status_code == 401

    valid_token_response = client.patch(
        f"/api/admin/offers/{offer_id}/moderation",
        headers=ADMIN_HEADERS,
        json={"is_public": True, "public_value": 2000},
    )
    assert valid_token_response.status_code == 200
    assert valid_token_response.json()["is_public"] is True
    assert valid_token_response.json()["status"] == "published"
    assert valid_token_response.json()["public_value"] == 2000


def test_public_offer_endpoints_do_not_require_admin_token(client: TestClient):
    list_response = client.get("/api/offers")

    assert list_response.status_code == 200


def test_create_or_get_telegram_user_endpoint(client: TestClient):
    first_response = client.post(
        "/api/users/telegram",
        json={
            "telegram_id": "123456789",
            "display_name": "Telegram User",
        },
    )
    assert first_response.status_code == 200
    first_user = first_response.json()
    assert first_user["id"]
    assert first_user["telegram_id"] == "123456789"
    assert first_user["display_name"] == "Telegram User"

    second_response = client.post(
        "/api/users/telegram",
        json={
            "telegram_id": "123456789",
            "display_name": "Updated Telegram User",
        },
    )
    assert second_response.status_code == 200
    second_user = second_response.json()
    assert second_user["id"] == first_user["id"]
    assert second_user["display_name"] == "Updated Telegram User"
