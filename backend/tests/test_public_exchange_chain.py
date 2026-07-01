from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.db.models.deal import Deal, DealStatus
from app.db.models.item import Item, ItemStatus, ItemType, OwnerType
from app.main import app


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


def create_item(
    db: Session,
    title: str,
    *,
    description: str | None = None,
    photo_url: str | None = None,
    is_public: bool = True,
) -> Item:
    item = Item(
        title=title,
        description=description,
        item_type=ItemType.PHYSICAL_ITEM.value,
        owner_type=OwnerType.PERSONAL.value,
        status=ItemStatus.ACTIVE.value,
        is_public=is_public,
        photo_url=photo_url,
    )
    db.add(item)
    db.flush()
    return item


def create_deal(
    db: Session,
    *,
    step_number: int,
    given_item: Item,
    received_item: Item,
    is_public: bool = True,
    status: str = DealStatus.COMPLETED.value,
    participant_visible: bool = True,
    participant_public_name: str | None = "Анна",
) -> Deal:
    deal = Deal(
        step_number=step_number,
        given_item_id=given_item.id,
        received_item_id=received_item.id,
        status=status,
        is_public=is_public,
        participant_visible=participant_visible,
        participant_public_name=participant_public_name,
        public_story=f"История шага {step_number}",
        deal_date=datetime(2026, 6, step_number, 12, 0, tzinfo=timezone.utc),
    )
    db.add(deal)
    db.flush()
    return deal


def seed_exchange_chain(db: Session) -> dict[str, Deal]:
    paperclip = create_item(
        db,
        "Скрепка",
        description="Обычная канцелярская скрепка",
        photo_url="/uploads/images/paperclip.jpg",
    )
    pen = create_item(
        db,
        "Ручка",
        description="Шариковая ручка",
        photo_url="/uploads/images/pen.jpg",
    )
    notebook = create_item(db, "Блокнот")
    mug = create_item(db, "Кружка")
    hidden_given = create_item(db, "Скрытый отданный предмет")
    hidden_received = create_item(db, "Скрытый полученный предмет")
    draft_given = create_item(db, "Черновик отдали")
    draft_received = create_item(db, "Черновик получили")

    second_deal = create_deal(
        db,
        step_number=2,
        given_item=pen,
        received_item=notebook,
        participant_visible=False,
        participant_public_name="Скрытый участник",
    )
    first_deal = create_deal(
        db,
        step_number=1,
        given_item=paperclip,
        received_item=pen,
        participant_public_name="Анна",
    )
    private_deal = create_deal(
        db,
        step_number=3,
        given_item=hidden_given,
        received_item=hidden_received,
        is_public=False,
        participant_public_name="Борис",
    )
    draft_deal = create_deal(
        db,
        step_number=4,
        given_item=draft_given,
        received_item=draft_received,
        status=DealStatus.NEW.value,
        participant_public_name="Вера",
    )
    item_hidden_deal = create_deal(
        db,
        step_number=5,
        given_item=create_item(db, "Непубличный item", is_public=False),
        received_item=mug,
        participant_public_name="Глеб",
    )
    db.commit()

    return {
        "first_deal": first_deal,
        "second_deal": second_deal,
        "private_deal": private_deal,
        "draft_deal": draft_deal,
        "item_hidden_deal": item_hidden_deal,
    }


def test_public_exchange_chain_returns_public_completed_deals_with_items(client):
    with next(app.dependency_overrides[get_db]()) as db:
        deals = seed_exchange_chain(db)

    response = client.get("/api/public/exchange-chain")

    assert response.status_code == 200
    payload = response.json()
    assert [deal["id"] for deal in payload] == [
        str(deals["first_deal"].id),
        str(deals["second_deal"].id),
    ]
    assert [deal["step_number"] for deal in payload] == [1, 2]
    assert payload[0]["status"] == DealStatus.COMPLETED.value
    assert payload[0]["given_item"] == {
        "id": str(deals["first_deal"].given_item_id),
        "title": "Скрепка",
        "description": "Обычная канцелярская скрепка",
        "photo_url": "/uploads/images/paperclip.jpg",
        "thumbnail_url": "/uploads/images/paperclip.jpg",
        "photo_urls": ["/uploads/images/paperclip.jpg"],
        "thumbnail_urls": ["/uploads/images/paperclip.jpg"],
    }
    assert payload[0]["received_item"]["title"] == "Ручка"
    assert payload[0]["received_item"]["photo_url"] == "/uploads/images/pen.jpg"
    assert payload[0]["received_item"]["thumbnail_url"] == "/uploads/images/pen.jpg"
    assert payload[0]["received_item"]["photo_urls"] == ["/uploads/images/pen.jpg"]
    assert payload[0]["received_item"]["thumbnail_urls"] == ["/uploads/images/pen.jpg"]


def test_public_exchange_chain_hides_invisible_participant(client):
    with next(app.dependency_overrides[get_db]()) as db:
        seed_exchange_chain(db)

    response = client.get("/api/public/exchange-chain")

    assert response.status_code == 200
    second_deal = response.json()[1]
    assert second_deal["participant_visible"] is False
    assert second_deal["participant_public_name"] is None
