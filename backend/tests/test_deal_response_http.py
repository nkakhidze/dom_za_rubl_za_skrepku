from collections.abc import Generator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
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


def create_user(client: TestClient, telegram_id: str) -> dict:
    response = client.post(
        "/api/users/telegram",
        json={
            "telegram_id": telegram_id,
            "display_name": f"User {telegram_id}",
        },
    )
    assert response.status_code == 200
    return response.json()


def upload_test_image(client: TestClient) -> str:
    image_bytes = BytesIO()
    Image.new("RGB", (24, 24), (20, 120, 90)).save(image_bytes, format="PNG")
    image_bytes.seek(0)

    response = client.post(
        "/api/files/images",
        files={
            "file": (
                "offer.png",
                image_bytes.getvalue(),
                "image/png",
            )
        },
    )
    assert response.status_code == 201
    return response.json()["photo_url"]


def create_offer_for_user(client: TestClient, telegram_id: str, title: str) -> dict:
    photo_url = upload_test_image(client)
    response = client.post(
        "/api/offers",
        json={
            "messenger_type": "telegram",
            "external_user_id": telegram_id,
            "username": telegram_id,
            "first_name": "Offer",
            "last_name": "Owner",
            "title": title,
            "description": "A useful physical item for deal response tests.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 3500,
            "photo_urls": [photo_url],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": True,
            "participant_public_name": f"Owner {telegram_id}",
        },
    )
    assert response.status_code == 201
    return response.json()


def publish_offer(client: TestClient, offer_id: str) -> dict:
    response = client.patch(
        f"/api/admin/offers/{offer_id}/moderation",
        headers=ADMIN_HEADERS,
        json={
            "is_public": True,
            "public_value": 3000,
            "public_comment": "Published for deal response tests.",
        },
    )
    assert response.status_code == 200
    return response.json()


def create_item(client: TestClient, user_id: str, title: str) -> dict:
    response = client.post(
        "/api/items",
        json={
            "user_id": user_id,
            "title": title,
            "description": "Item offered in exchange.",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_user_can_create_item_and_see_only_own_items(client: TestClient):
    first_user = create_user(client, "item-owner-1")
    second_user = create_user(client, "item-owner-2")
    first_item = create_item(client, first_user["id"], "First user item")
    second_item = create_item(client, second_user["id"], "Second user item")

    first_items_response = client.get(f"/api/users/{first_user['id']}/items")

    assert first_items_response.status_code == 200
    first_items = first_items_response.json()
    assert [item["id"] for item in first_items] == [first_item["id"]]
    assert first_item["status"] == "active"
    assert second_item["id"] not in {item["id"] for item in first_items}


def test_missing_user_items_returns_404(client: TestClient):
    response = client.get("/api/users/00000000-0000-0000-0000-000000000001/items")

    assert response.status_code == 404


def test_cannot_create_deal_for_non_public_offer(client: TestClient):
    offer_owner = create_user(client, "private-offer-owner")
    responder = create_user(client, "private-offer-responder")
    offer = create_offer_for_user(client, "private-offer-owner", "Private deal offer")
    item = create_item(client, responder["id"], "Responder item")

    response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": item["id"],
        },
    )

    assert offer_owner["id"]
    assert response.status_code == 400


def test_user_can_create_deal_for_published_offer_and_admin_updates_status(
    client: TestClient,
):
    offer_owner = create_user(client, "published-offer-owner")
    responder = create_user(client, "published-offer-responder")
    offer = create_offer_for_user(client, "published-offer-owner", "Published deal offer")
    published_offer = publish_offer(client, offer["id"])
    item = create_item(client, responder["id"], "Responder exchange item")

    response = client.post(
        "/api/deals",
        json={
            "offer_id": published_offer["id"],
            "item_id": item["id"],
        },
    )

    assert offer_owner["id"]
    assert response.status_code == 201
    deal = response.json()
    assert deal["offer_id"] == published_offer["id"]
    assert deal["item_id"] == item["id"]
    assert deal["status"] == "new"

    item_owner_deals_response = client.get(f"/api/users/{responder['id']}/deals")
    assert item_owner_deals_response.status_code == 200
    item_owner_deals = item_owner_deals_response.json()
    assert item_owner_deals[0]["id"] == deal["id"]
    assert item_owner_deals[0]["offer_title"] == "Published deal offer"
    assert item_owner_deals[0]["item_title"] == "Responder exchange item"

    offer_owner_deals_response = client.get(f"/api/users/{offer_owner['id']}/deals")
    assert offer_owner_deals_response.status_code == 200
    assert offer_owner_deals_response.json()[0]["id"] == deal["id"]

    admin_list_missing_token = client.get("/api/admin/deals")
    assert admin_list_missing_token.status_code == 401

    admin_list_response = client.get("/api/admin/deals", headers=ADMIN_HEADERS)
    assert admin_list_response.status_code == 200
    admin_list_deal = next(
        admin_deal
        for admin_deal in admin_list_response.json()
        if admin_deal["deal_id"] == deal["id"]
    )
    assert admin_list_deal["offer_title"] == "Published deal offer"
    assert admin_list_deal["item_title"] == "Responder exchange item"
    assert admin_list_deal["offer_owner_user_id"] == offer_owner["id"]
    assert admin_list_deal["item_owner_user_id"] == responder["id"]

    admin_detail_response = client.get(
        f"/api/admin/deals/{deal['id']}",
        headers=ADMIN_HEADERS,
    )
    assert admin_detail_response.status_code == 200
    admin_detail = admin_detail_response.json()
    assert admin_detail["id"] == deal["id"]
    assert admin_detail["offer"]["title"] == "Published deal offer"
    assert admin_detail["item"]["title"] == "Responder exchange item"
    assert admin_detail["offer_owner"]["id"] == offer_owner["id"]
    assert admin_detail["item_owner"]["id"] == responder["id"]

    status_response = client.patch(
        f"/api/admin/deals/{deal['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "accepted"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "accepted"
    assert status_response.json()["status_label"] == "Принята"

    invalid_status_response = client.patch(
        f"/api/admin/deals/{deal['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "unknown"},
    )
    assert invalid_status_response.status_code == 422

    missing_deal_status_response = client.patch(
        "/api/admin/deals/00000000-0000-0000-0000-000000000001/status",
        headers=ADMIN_HEADERS,
        json={"status": "accepted"},
    )
    assert missing_deal_status_response.status_code == 404


def test_create_deal_validation_errors(client: TestClient):
    offer_owner = create_user(client, "validation-offer-owner")
    responder = create_user(client, "validation-responder")
    offer = publish_offer(
        client,
        create_offer_for_user(client, "validation-offer-owner", "Validation offer")["id"],
    )
    item = create_item(client, responder["id"], "Validation item")

    missing_offer_response = client.post(
        "/api/deals",
        json={
            "offer_id": "00000000-0000-0000-0000-000000000001",
            "item_id": item["id"],
        },
    )
    assert missing_offer_response.status_code == 404

    missing_item_response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": "00000000-0000-0000-0000-000000000002",
        },
    )
    assert missing_item_response.status_code == 404

    owner_item = create_item(client, offer_owner["id"], "Own response item")
    own_offer_response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": owner_item["id"],
        },
    )
    assert own_offer_response.status_code == 400

    first_deal_response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": item["id"],
        },
    )
    assert first_deal_response.status_code == 201

    duplicate_deal_response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": item["id"],
        },
    )
    assert duplicate_deal_response.status_code == 400


def test_public_offers_still_work_with_deals_enabled(client: TestClient):
    create_user(client, "public-offer-owner")
    offer = create_offer_for_user(client, "public-offer-owner", "Public offer still works")
    publish_offer(client, offer["id"])

    response = client.get("/api/offers")

    assert response.status_code == 200
    assert offer["id"] in {public_offer["id"] for public_offer in response.json()}


def test_deal_notifications_are_sent_for_create_and_status_update(
    client: TestClient,
    monkeypatch,
):
    class FakeNotificationService:
        def __init__(self) -> None:
            self.messages: list[tuple[str, str]] = []

        def send_telegram_message(self, telegram_id: str, text: str) -> bool:
            self.messages.append((telegram_id, text))
            return True

    notifications = FakeNotificationService()
    monkeypatch.setattr(
        "app.services.deal_service.TelegramNotificationService",
        lambda: notifications,
    )

    offer_owner = create_user(client, "deal-notify-owner")
    responder = create_user(client, "deal-notify-responder")
    offer = publish_offer(
        client,
        create_offer_for_user(client, "deal-notify-owner", "Notification deal offer")["id"],
    )
    item = create_item(client, responder["id"], "Notification response item")

    deal_response = client.post(
        "/api/deals",
        json={
            "offer_id": offer["id"],
            "item_id": item["id"],
        },
    )

    assert offer_owner["telegram_id"] == "deal-notify-owner"
    assert deal_response.status_code == 201
    assert notifications.messages[0][0] == "deal-notify-owner"
    assert "новый отклик" in notifications.messages[0][1]

    status_response = client.patch(
        f"/api/admin/deals/{deal_response.json()['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "accepted"},
    )

    assert status_response.status_code == 200
    notified_telegram_ids = {telegram_id for telegram_id, _ in notifications.messages}
    assert {"deal-notify-owner", "deal-notify-responder"}.issubset(notified_telegram_ids)
    assert any("принят" in text for _, text in notifications.messages)
