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


ADMIN_HEADERS = {"Authorization": "Bearer test_admin_token"}


@pytest.fixture()
def client(monkeypatch) -> Generator[TestClient, None, None]:
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
    monkeypatch.setattr(settings, "admin_api_token", "test_admin_token")
    monkeypatch.setattr(settings, "allow_admin_token_auth", True)

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


def create_offer(client: TestClient, title: str = "Книга", declared_value: int = 1000) -> dict:
    response = client.post(
        "/api/offers",
        json={
            "messenger_type": "web",
            "external_user_id": f"user-{title}",
            "title": title,
            "description": "Хороший предмет для следующего обмена.",
            "offer_type": "physical_item",
            "city": "Томск",
            "declared_value": declared_value,
            "photo_urls": ["/uploads/images/item.jpg"],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": True,
            "participant_public_name": "Анна",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_admin_offer_value_sort_promotes_admin_valued_offers(client: TestClient):
    high_user_value = create_offer(client, title="value-5", declared_value=5)
    middle_user_value = create_offer(client, title="value-4", declared_value=4)
    low_user_value = create_offer(client, title="value-3", declared_value=3)

    initial_response = client.get(
        "/api/admin/offers",
        headers=ADMIN_HEADERS,
        params={"sort": "value_desc"},
    )
    assert initial_response.status_code == 200
    assert [offer["id"] for offer in initial_response.json()[:3]] == [
        high_user_value["id"],
        middle_user_value["id"],
        low_user_value["id"],
    ]

    moderation_response = client.patch(
        f"/api/admin/offers/{low_user_value['id']}/moderation",
        headers=ADMIN_HEADERS,
        json={"moderated_value": 2},
    )
    assert moderation_response.status_code == 200

    sorted_response = client.get(
        "/api/admin/offers",
        headers=ADMIN_HEADERS,
        params={"sort": "value_desc"},
    )
    assert sorted_response.status_code == 200
    assert [offer["id"] for offer in sorted_response.json()[:3]] == [
        low_user_value["id"],
        high_user_value["id"],
        middle_user_value["id"],
    ]


def create_current_item(client: TestClient) -> dict:
    response = client.post(
        "/api/admin/items",
        headers=ADMIN_HEADERS,
        json={
            "title": "Скрепка",
            "description": "Стартовый предмет",
            "item_type": "physical_item",
            "owner_type": "tom_sawyer_fest",
            "owner_name": "Проект",
            "is_current": True,
            "is_public": True,
            "sequence_number": 0,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_offer_with_photos(client: TestClient, photo_urls: list[str]) -> dict:
    response = client.post(
        "/api/offers",
        json={
            "messenger_type": "web",
            "external_user_id": "user-with-many-photos",
            "title": "Photo item",
            "description": "Item with several photos for chain selection.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 1000,
            "photo_urls": photo_urls,
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": True,
            "participant_public_name": "Anna",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_admin_can_set_offer_visibility_and_priority(client: TestClient):
    offer = create_offer(client)

    response = client.patch(
        f"/api/admin/offers/{offer['id']}/moderation",
        headers=ADMIN_HEADERS,
        json={
            "moderated_value": 1500,
            "visibility_status": "low_priority",
            "sort_priority": -10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["moderated_value"] == 1500
    assert payload["visibility_status"] == "low_priority"
    assert payload["sort_priority"] == -10
    assert payload["status"] == "new"


def test_select_next_creates_chain_item_and_deal(client: TestClient):
    previous_item = create_current_item(client)
    offer = create_offer(client, "Ручка")

    response = client.post(
        f"/api/admin/offers/{offer['id']}/select-next",
        headers=ADMIN_HEADERS,
        json={
            "public_story": "Скрепку обменяли на ручку.",
            "photo_url": "/uploads/images/pen.jpg",
            "is_public": True,
        },
    )

    assert response.status_code == 201
    deal = response.json()
    assert deal["step_number"] == 1
    assert deal["given_item_id"] == previous_item["id"]
    assert deal["status"] == "completed"
    assert deal["is_public"] is True

    selected_offer_response = client.get(
        f"/api/admin/offers/{offer['id']}",
        headers=ADMIN_HEADERS,
    )
    assert selected_offer_response.status_code == 200
    assert selected_offer_response.json()["status"] == "selected"

    items_response = client.get("/api/admin/items", headers=ADMIN_HEADERS)
    assert items_response.status_code == 200
    items = items_response.json()
    current_items = [item for item in items if item["is_current"]]
    assert len(current_items) == 1
    assert current_items[0]["title"] == "Ручка"
    assert current_items[0]["status"] == "current"
    assert current_items[0]["source_offer_id"] == offer["id"]

    previous_item_after = next(item for item in items if item["id"] == previous_item["id"])
    assert previous_item_after["is_current"] is False
    assert previous_item_after["status"] == "past"

    history_response = client.get("/api/public/exchange-chain")
    assert history_response.status_code == 200
    assert history_response.json()[0]["received_item"]["title"] == "Ручка"


def test_select_next_transfers_all_offer_photos_to_item_and_avatar_is_first_photo(
    client: TestClient,
):
    create_current_item(client)
    photo_urls = [
        "/uploads/images/first.jpg",
        "/uploads/images/second.jpg",
        "/uploads/images/third.jpg",
    ]
    offer = create_offer_with_photos(client, photo_urls)

    response = client.post(
        f"/api/admin/offers/{offer['id']}/select-next",
        headers=ADMIN_HEADERS,
        json={"is_public": True},
    )

    assert response.status_code == 201

    items_response = client.get("/api/admin/items", headers=ADMIN_HEADERS)
    assert items_response.status_code == 200
    selected_item = next(
        item for item in items_response.json() if item["source_offer_id"] == offer["id"]
    )
    assert selected_item["photo_url"] == photo_urls[0]
    assert selected_item["photo_urls"] == photo_urls
    assert [photo["photo_url"] for photo in selected_item["photos"]] == photo_urls

    history_response = client.get("/api/public/exchange-chain")
    assert history_response.status_code == 200
    received_item = history_response.json()[0]["received_item"]
    assert received_item["photo_url"] == photo_urls[0]
    assert received_item["photo_urls"] == photo_urls

    first_photo_id = selected_item["photos"][0]["id"]
    delete_response = client.delete(
        f"/api/admin/items/{selected_item['id']}/photos/{first_photo_id}",
        headers=ADMIN_HEADERS,
    )
    assert delete_response.status_code == 204

    updated_items_response = client.get("/api/admin/items", headers=ADMIN_HEADERS)
    assert updated_items_response.status_code == 200
    updated_item = next(
        item for item in updated_items_response.json() if item["id"] == selected_item["id"]
    )
    assert updated_item["photo_url"] == photo_urls[1]
    assert updated_item["photo_urls"] == photo_urls[1:]


def test_cannot_select_same_or_rejected_offer(client: TestClient):
    create_current_item(client)
    offer = create_offer(client, "Телефон")

    first_response = client.post(
        f"/api/admin/offers/{offer['id']}/select-next",
        headers=ADMIN_HEADERS,
        json={"is_public": True},
    )
    assert first_response.status_code == 201

    duplicate_response = client.post(
        f"/api/admin/offers/{offer['id']}/select-next",
        headers=ADMIN_HEADERS,
        json={"is_public": True},
    )
    assert duplicate_response.status_code == 400

    rejected_offer = create_offer(client, "Часы")
    reject_response = client.patch(
        f"/api/admin/offers/{rejected_offer['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "rejected"},
    )
    assert reject_response.status_code == 200

    rejected_select_response = client.post(
        f"/api/admin/offers/{rejected_offer['id']}/select-next",
        headers=ADMIN_HEADERS,
        json={"is_public": True},
    )
    assert rejected_select_response.status_code == 400
