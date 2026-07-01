from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.db.models.auth import AuthAccount, RoleCode
from app.main import app
from app.services.auth_service import AuthService


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
    monkeypatch.setattr(settings, "dev_mode", True)

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


def create_auth_user_with_role(client: TestClient, login: str, role: str) -> str:
    db_generator = next(iter(app.dependency_overrides.values()))()
    db = next(db_generator)
    try:
        service = AuthService(db)
        service.ensure_initial_roles()
        user = service.create_auth_user(login, "password", display_name=login)
        if role != RoleCode.USER.value:
            service.assign_role(user.id, role, assigned_by_user_id=None)
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

    response = client.post(
        "/api/auth/login",
        json={"login": login, "password": "password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient):
    create_auth_user_with_role(client, "auth-user", RoleCode.USER.value)

    response = client.post(
        "/api/auth/login",
        json={"login": "auth-user", "password": "wrong"},
    )

    assert response.status_code == 401


def test_login_rejects_missing_login_like_wrong_password(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"login": "missing-user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login or password"


def test_inactive_auth_account_cannot_login(client: TestClient):
    create_auth_user_with_role(client, "inactive-auth", RoleCode.USER.value)
    db_generator = next(iter(app.dependency_overrides.values()))()
    db = next(db_generator)

    try:
        auth_account = db.scalar(
            select(AuthAccount).where(AuthAccount.login == "inactive-auth")
        )
        auth_account.is_active = False
        db.commit()
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

    response = client.post(
        "/api/auth/login",
        json={"login": "inactive-auth", "password": "password"},
    )

    assert response.status_code == 401


def test_login_and_me_return_user_roles(client: TestClient):
    token = create_auth_user_with_role(client, "auth-admin", RoleCode.ADMIN.value)

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["display_name"] == "auth-admin"
    assert response.json()["login"] == "auth-admin"
    assert response.json()["is_active"] is True
    assert "admin" in response.json()["roles"]


def test_admin_offers_requires_token(client: TestClient):
    response = client.get("/api/admin/offers")

    assert response.status_code == 401


def test_corrupted_jwt_is_rejected(client: TestClient):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer broken.token.value"},
    )

    assert response.status_code == 401


def test_expired_jwt_is_rejected(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    token = create_auth_user_with_role(client, "expired-user", RoleCode.USER.value)

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_admin_offers_rejects_user_role(client: TestClient):
    token = create_auth_user_with_role(client, "plain-user", RoleCode.USER.value)

    response = client.get("/api/admin/offers", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_editor_can_read_offers_but_cannot_moderate(client: TestClient):
    token = create_auth_user_with_role(client, "editor-user", RoleCode.EDITOR.value)

    list_response = client.get(
        "/api/admin/offers",
        headers={"Authorization": f"Bearer {token}"},
    )
    moderation_response = client.patch(
        "/api/admin/offers/00000000-0000-0000-0000-000000000001/moderation",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_public": True},
    )

    assert list_response.status_code == 200
    assert moderation_response.status_code == 403


def test_admin_offers_allows_moderator_role(client: TestClient):
    token = create_auth_user_with_role(client, "moderator-user", RoleCode.MODERATOR.value)

    response = client.get("/api/admin/offers", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_moderator_can_reach_moderation_endpoint(client: TestClient):
    token = create_auth_user_with_role(client, "moderator-patch-user", RoleCode.MODERATOR.value)

    response = client.patch(
        "/api/admin/offers/00000000-0000-0000-0000-000000000001/moderation",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_public": True},
    )

    assert response.status_code == 404


def test_admin_can_assign_moderator_but_not_super_admin(client: TestClient):
    admin_token = create_auth_user_with_role(client, "role-admin", RoleCode.ADMIN.value)
    user_token = create_auth_user_with_role(client, "target-user", RoleCode.USER.value)
    user_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    user_id = user_response.json()["id"]

    moderator_response = client.post(
        f"/api/admin/users/{user_id}/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "moderator"},
    )
    assert moderator_response.status_code == 200
    assert "moderator" in moderator_response.json()["roles"]

    admin_response = client.post(
        f"/api/admin/users/{user_id}/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "admin"},
    )
    assert admin_response.status_code == 403

    super_admin_response = client.post(
        f"/api/admin/users/{user_id}/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "super_admin"},
    )
    assert super_admin_response.status_code == 403


def test_super_admin_can_assign_admin_and_last_super_admin_cannot_be_removed(
    client: TestClient,
):
    super_token = create_auth_user_with_role(client, "root-user", RoleCode.SUPER_ADMIN.value)
    user_token = create_auth_user_with_role(client, "admin-target", RoleCode.USER.value)
    user_id = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    ).json()["id"]
    root_id = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {super_token}"},
    ).json()["id"]

    assign_response = client.post(
        f"/api/admin/users/{user_id}/roles",
        headers={"Authorization": f"Bearer {super_token}"},
        json={"role": "admin"},
    )
    assert assign_response.status_code == 200
    assert "admin" in assign_response.json()["roles"]

    remove_response = client.delete(
        f"/api/admin/users/{root_id}/roles/super_admin",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert remove_response.status_code == 400


def test_removed_role_takes_effect_without_waiting_for_jwt_expiry(client: TestClient):
    super_token = create_auth_user_with_role(client, "role-remover", RoleCode.SUPER_ADMIN.value)
    moderator_token = create_auth_user_with_role(client, "soon-plain-user", RoleCode.MODERATOR.value)
    moderator_id = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {moderator_token}"},
    ).json()["id"]

    before_response = client.patch(
        "/api/admin/offers/00000000-0000-0000-0000-000000000001/moderation",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={"is_public": True},
    )
    assert before_response.status_code == 404

    remove_response = client.delete(
        f"/api/admin/users/{moderator_id}/roles/moderator",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert remove_response.status_code == 204

    after_response = client.patch(
        "/api/admin/offers/00000000-0000-0000-0000-000000000001/moderation",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={"is_public": True},
    )
    assert after_response.status_code == 403


def test_admin_token_fallback_can_be_disabled(client: TestClient, monkeypatch):
    headers = {"Authorization": "Bearer test_admin_token"}

    allowed_response = client.get("/api/admin/offers", headers=headers)
    assert allowed_response.status_code == 200

    monkeypatch.setattr(settings, "allow_admin_token_auth", False)
    denied_response = client.get("/api/admin/offers", headers=headers)
    assert denied_response.status_code == 401


def test_dev_phone_verification_and_verified_phone_lookup(client: TestClient):
    token = create_auth_user_with_role(client, "phone-user", RoleCode.USER.value)
    user_id = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]

    set_phone_response = client.post(
        f"/api/users/{user_id}/phone",
        json={"phone": "+79990000000"},
    )
    assert set_phone_response.status_code == 200
    assert set_phone_response.json()["phone_verified"] is False

    verify_response = client.post(f"/api/users/{user_id}/phone/verify-dev")
    assert verify_response.status_code == 200
    assert verify_response.json()["phone_verified"] is True
