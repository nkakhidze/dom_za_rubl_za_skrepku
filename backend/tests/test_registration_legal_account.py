from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.db.models.auth import AuthAccount
from app.db.models.deal import Deal, DealStatus
from app.db.models.item import Item, ItemStatus, ItemType, OwnerType
from app.db.models.offer import ExchangePreference, Offer, OfferStatus, OfferType
from app.db.models.user_consent import UserConsent
from app.main import app
from app.services.legal_document_service import LegalDocumentService


def _legal_version(code: str) -> str:
    document = LegalDocumentService().get_active_document(code)
    assert document is not None
    return document.version


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
    monkeypatch.setattr(settings, "jwt_secret_key", "test-secret")
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


def _registration_payload(**overrides):
    payload = {
        "login": "new-user",
        "password": "strong-password",
        "password_confirmation": "strong-password",
        "display_name": "Николай",
        "phone": "+7 (999) 000-11-22",
        "email": None,
        "is_adult_confirmed": True,
        "user_agreement": {
            "accepted": True,
            "version": _legal_version("user_agreement"),
        },
        "personal_data_consent": {
            "accepted": True,
            "version": _legal_version("personal_data_consent"),
        },
        "privacy_policy_version": _legal_version("privacy_policy"),
        "marketing_consent": {
            "version": _legal_version("marketing_consent"),
            "email": False,
            "telegram": False,
            "max": False,
        },
    }
    payload.update(overrides)
    return payload


def test_legal_documents_are_public(client):
    response = client.get("/api/legal/documents")

    assert response.status_code == 200
    codes = {document["code"] for document in response.json()}
    assert "user_agreement" in codes
    assert "personal_data_consent" in codes


def test_registration_with_phone_and_without_email_creates_user_role_and_consents(client):
    response = client.post("/api/auth/register", json=_registration_payload())

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["phone"] == "+79990001122"
    assert payload["user"]["email"] is None
    assert payload["user"]["roles"] == ["user"]
    assert "password_hash" not in payload["user"]

    account = client.get(
        "/api/auth/account",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )

    assert account.status_code == 200
    consent_codes = {consent["document_code"] for consent in account.json()["consents"]}
    assert {
        "user_agreement",
        "personal_data_consent",
        "privacy_policy",
        "marketing_consent",
    }.issubset(consent_codes)


def test_registration_requires_phone(client):
    payload = _registration_payload()
    payload.pop("phone")

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422


def test_registration_rejects_empty_normalized_phone(client):
    response = client.post("/api/auth/register", json=_registration_payload(phone="------"))

    assert response.status_code == 400


def test_registration_requires_adult_checkbox(client):
    response = client.post(
        "/api/auth/register",
        json=_registration_payload(is_adult_confirmed=False),
    )

    assert response.status_code == 400


def test_registration_requires_user_agreement(client):
    payload = _registration_payload(
        user_agreement={
            "accepted": False,
            "version": _legal_version("user_agreement"),
        },
    )

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


def test_registration_rejects_non_current_document_version(client):
    payload = _registration_payload(
        user_agreement={
            "accepted": True,
            "version": "1900-01-01",
        },
    )

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


def test_registration_normalizes_login_and_rejects_duplicate(client):
    first = client.post("/api/auth/register", json=_registration_payload(login="Mixed.Login"))
    assert first.status_code == 201
    assert first.json()["user"]["login"] == "mixed.login"

    duplicate = client.post("/api/auth/register", json=_registration_payload(login="mixed.login"))
    assert duplicate.status_code == 400


def test_registration_request_cannot_assign_admin(client):
    payload = _registration_payload(role="admin", roles=["admin"])
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["user"]["roles"] == ["user"]


def test_marketing_channels_can_be_changed_independently(client):
    register = client.post("/api/auth/register", json=_registration_payload(login="marketing-user"))
    token = register.json()["access_token"]

    response = client.patch(
        "/api/auth/me/consents/marketing",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "document_version": _legal_version("marketing_consent"),
            "email": True,
            "telegram": False,
            "max": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["consent_payload"]["channels"] == {
        "email": True,
        "telegram": False,
        "max": False,
    }

    account = client.get("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
    marketing_records = [
        consent
        for consent in account.json()["consents"]
        if consent["document_code"] == "marketing_consent"
    ]
    assert any(consent["status"] == "revoked" for consent in marketing_records)
    assert any(consent["status"] == "accepted" for consent in marketing_records)


def test_account_requires_authentication(client):
    response = client.get("/api/auth/account")

    assert response.status_code == 401


def test_registration_stores_hash_and_consent_history(client):
    register = client.post("/api/auth/register", json=_registration_payload(login="stored-user"))
    user_id = UUID(register.json()["user"]["id"])

    db_generator = next(iter(client.app.dependency_overrides.values()))()
    db = next(db_generator)
    try:
        auth_account = db.scalar(select(AuthAccount).where(AuthAccount.user_id == user_id))
        consents = db.scalars(select(UserConsent).where(UserConsent.user_id == user_id)).all()
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

    assert auth_account.password_hash != "strong-password"
    assert len(consents) >= 4
    expected_versions = {
        "user_agreement": _legal_version("user_agreement"),
        "personal_data_consent": _legal_version("personal_data_consent"),
        "privacy_policy": _legal_version("privacy_policy"),
        "marketing_consent": _legal_version("marketing_consent"),
    }
    assert all(
        consent.document_version == expected_versions[consent.document_code]
        for consent in consents
    )
    assert all(consent.source == "web" for consent in consents)


def test_account_profile_can_be_updated(client):
    register = client.post("/api/auth/register", json=_registration_payload(login="profile-user"))
    token = register.json()["access_token"]

    response = client.patch(
        "/api/auth/account",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Updated User",
            "phone": "+7 (999) 111-22-33",
            "email": "USER@Example.COM",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated User"
    assert response.json()["phone"] == "+79991112233"
    assert response.json()["phone_verified"] is False
    assert response.json()["email"] == "user@example.com"


def test_my_offers_uses_current_user_from_jwt(client):
    first_register = client.post("/api/auth/register", json=_registration_payload(login="owner-one"))
    second_register = client.post("/api/auth/register", json=_registration_payload(login="owner-two"))
    first_token = first_register.json()["access_token"]
    first_user_id = UUID(first_register.json()["user"]["id"])
    second_user_id = UUID(second_register.json()["user"]["id"])

    with next(app.dependency_overrides[get_db]()) as db:
        db.add_all(
            [
                Offer(
                    user_id=first_user_id,
                    title="First user offer",
                    description="First user private item",
                    offer_type=OfferType.PHYSICAL_ITEM.value,
                    city="Tomsk",
                    declared_value=100,
                    exchange_preference=ExchangePreference.ANY_OFFER.value,
                    status=OfferStatus.NEW.value,
                    consent_accepted=True,
                ),
                Offer(
                    user_id=second_user_id,
                    title="Second user offer",
                    description="Second user private item",
                    offer_type=OfferType.PHYSICAL_ITEM.value,
                    city="Tomsk",
                    declared_value=200,
                    exchange_preference=ExchangePreference.ANY_OFFER.value,
                    status=OfferStatus.NEW.value,
                    consent_accepted=True,
                ),
            ]
        )
        db.commit()

    response = client.get("/api/auth/me/offers", headers={"Authorization": f"Bearer {first_token}"})

    assert response.status_code == 200
    assert [offer["title"] for offer in response.json()] == ["First user offer"]
    assert "user_id" not in response.json()[0]


def test_create_offer_with_jwt_belongs_to_current_user(client):
    register = client.post("/api/auth/register", json=_registration_payload(login="offer-jwt-owner"))
    token = register.json()["access_token"]
    user_id = UUID(register.json()["user"]["id"])

    create_response = client.post(
        "/api/offers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "messenger_type": "web",
            "external_user_id": "browser-local-user-id",
            "username": None,
            "first_name": None,
            "last_name": None,
            "title": "JWT linked proposal",
            "description": "Proposal created by an authenticated web user",
            "offer_type": OfferType.SERVICE.value,
            "city": "Tomsk",
            "declared_value": 100,
            "photo_urls": [],
            "exchange_preference": ExchangePreference.ANY_OFFER.value,
            "consent_accepted": True,
            "participant_visible": False,
            "participant_public_name": None,
        },
    )

    assert create_response.status_code == 201
    offer_id = UUID(create_response.json()["id"])

    with next(app.dependency_overrides[get_db]()) as db:
        offer = db.get(Offer, offer_id)

    assert offer is not None
    assert offer.user_id == user_id

    response = client.get("/api/auth/me/offers", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert [offer["title"] for offer in response.json()] == ["JWT linked proposal"]


def test_my_deals_uses_current_user_from_jwt(client):
    first_register = client.post("/api/auth/register", json=_registration_payload(login="deal-owner-one"))
    second_register = client.post("/api/auth/register", json=_registration_payload(login="deal-owner-two"))
    first_token = first_register.json()["access_token"]
    first_user_id = UUID(first_register.json()["user"]["id"])
    second_user_id = UUID(second_register.json()["user"]["id"])

    with next(app.dependency_overrides[get_db]()) as db:
        first_offer = Offer(
            user_id=first_user_id,
            title="Owner deal offer",
            description="Owner deal offer description",
            offer_type=OfferType.PHYSICAL_ITEM.value,
            city="Tomsk",
            declared_value=100,
            exchange_preference=ExchangePreference.ANY_OFFER.value,
            status=OfferStatus.NEW.value,
            consent_accepted=True,
        )
        second_offer = Offer(
            user_id=second_user_id,
            title="Other deal offer",
            description="Other deal offer description",
            offer_type=OfferType.PHYSICAL_ITEM.value,
            city="Tomsk",
            declared_value=200,
            exchange_preference=ExchangePreference.ANY_OFFER.value,
            status=OfferStatus.NEW.value,
            consent_accepted=True,
        )
        first_item = Item(
            user_id=first_user_id,
            title="First user item",
            description="First user item description",
            item_type=ItemType.PHYSICAL_ITEM.value,
            owner_type=OwnerType.PERSONAL.value,
            status=ItemStatus.ACTIVE.value,
            is_public=False,
        )
        second_item = Item(
            user_id=second_user_id,
            title="Second user item",
            description="Second user item description",
            item_type=ItemType.PHYSICAL_ITEM.value,
            owner_type=OwnerType.PERSONAL.value,
            status=ItemStatus.ACTIVE.value,
            is_public=False,
        )
        db.add_all([first_offer, second_offer, first_item, second_item])
        db.flush()
        db.add_all(
            [
                Deal(
                    offer_id=first_offer.id,
                    step_number=101,
                    given_item_id=first_item.id,
                    received_item_id=second_item.id,
                    status=DealStatus.NEW.value,
                ),
                Deal(
                    offer_id=second_offer.id,
                    step_number=102,
                    given_item_id=second_item.id,
                    received_item_id=first_item.id,
                    status=DealStatus.NEW.value,
                ),
            ]
        )
        db.commit()

    response = client.get("/api/auth/me/deals", headers={"Authorization": f"Bearer {first_token}"})

    assert response.status_code == 200
    assert {deal["offer_title"] for deal in response.json()} == {
        "Owner deal offer",
        "Other deal offer",
    }
    assert all("user_id" not in deal for deal in response.json())
