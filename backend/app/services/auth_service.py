import base64
import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.auth import AuthAccount, INITIAL_ROLES, Role, RoleCode, UserRole
from app.db.models.user import User
from app.db.models.user_consent import ConsentSource, ConsentStatus, UserConsent
from app.schemas.auth import MarketingConsentRequest, RegisterRequest
from app.services.legal_document_service import LegalDocumentService


logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


class AuthService:
    PASSWORD_ITERATIONS = 260_000
    LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
    RESERVED_LOGINS = {
        "admin",
        "administrator",
        "api",
        "auth",
        "login",
        "logout",
        "register",
        "root",
        "super_admin",
        "support",
        "system",
    }

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.PASSWORD_ITERATIONS,
        )
        return (
            f"pbkdf2_sha256${cls.PASSWORD_ITERATIONS}$"
            f"{_b64url_encode(salt)}${_b64url_encode(password_hash)}"
        )

    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, expected_hash_text = password_hash.split("$", 3)
            iterations = int(iterations_text)
        except ValueError:
            return False

        if algorithm != "pbkdf2_sha256":
            return False

        salt = _b64url_decode(salt_text)
        expected_hash = _b64url_decode(expected_hash_text)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual_hash, expected_hash)

    def authenticate(self, login: str, password: str) -> User | None:
        normalized_login = self.normalize_login(login)
        auth_account = self.db.scalar(
            select(AuthAccount).where(
                AuthAccount.login == normalized_login,
            )
        )

        if auth_account is None:
            logger.warning(
                "Auth login failed: login=%s reason=auth_account_not_found",
                normalized_login,
            )
            return None

        if not auth_account.is_active:
            logger.warning(
                "Auth login failed: login=%s user_id=%s reason=auth_account_inactive",
                normalized_login,
                auth_account.user_id,
            )
            return None

        if not auth_account.user.is_active:
            logger.warning(
                "Auth login failed: login=%s user_id=%s reason=user_inactive",
                normalized_login,
                auth_account.user_id,
            )
            return None

        if not self.verify_password(password, auth_account.password_hash):
            logger.warning(
                "Auth login failed: login=%s user_id=%s reason=password_mismatch",
                normalized_login,
                auth_account.user_id,
            )
            return None

        logger.info(
            "Auth login succeeded: login=%s user_id=%s",
            normalized_login,
            auth_account.user_id,
        )
        return auth_account.user

    def create_access_token(self, user: User) -> str:
        now = int(time.time())
        payload = {
            "sub": str(user.id),
            "iat": now,
            "exp": now + settings.access_token_expire_minutes * 60,
            "roles": self.get_user_roles(user),
        }
        header = {
            "alg": settings.jwt_algorithm,
            "typ": "JWT",
        }
        signing_input = (
            f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
            f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
        )
        signature = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{signing_input}.{_b64url_encode(signature)}"

    def decode_access_token(self, token: str) -> dict | None:
        try:
            header_text, payload_text, signature_text = token.split(".", 2)
        except ValueError:
            return None

        signing_input = f"{header_text}.{payload_text}"
        expected_signature = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(_b64url_encode(expected_signature), signature_text):
            return None

        try:
            payload = json.loads(_b64url_decode(payload_text))
        except json.JSONDecodeError:
            return None

        if int(payload.get("exp", 0)) < int(time.time()):
            return None

        return payload

    def get_user_roles(self, user: User) -> list[str]:
        return sorted(user_role.role.code for user_role in user.user_roles)

    def ensure_initial_roles(self) -> None:
        existing_codes = set(self.db.scalars(select(Role.code)).all())

        for code, name in INITIAL_ROLES.items():
            if code not in existing_codes:
                self.db.add(Role(code=code, name=name))

        self.db.commit()

    @classmethod
    def normalize_login(cls, login: str) -> str:
        return login.strip().lower()

    @classmethod
    def normalize_phone(cls, phone: str | None) -> str | None:
        if phone is None:
            return None

        normalized = re.sub(r"[^\d+]", "", phone.strip())
        return normalized or None

    @classmethod
    def normalize_email(cls, email: str | None) -> str | None:
        if email is None:
            return None

        normalized = email.strip().lower()
        return normalized or None

    @classmethod
    def validate_login(cls, login: str) -> str:
        normalized = cls.normalize_login(login)

        if len(normalized) < 3 or len(normalized) > 50:
            raise ValueError("Логин должен быть от 3 до 50 символов")

        if normalized in cls.RESERVED_LOGINS:
            raise ValueError("Этот логин зарезервирован")

        if not cls.LOGIN_PATTERN.match(normalized):
            raise ValueError("Логин может содержать только буквы, цифры, _, - и .")

        return normalized

    @classmethod
    def validate_email(cls, email: str | None) -> str | None:
        normalized = cls.normalize_email(email)

        if normalized is None:
            return None

        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Некорректный email")

        return normalized

    def register_user(
        self,
        request: RegisterRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
        source: str = ConsentSource.WEB.value,
    ) -> User:
        self.ensure_initial_roles()
        legal_service = LegalDocumentService()
        now = utc_now()

        login = self.validate_login(request.login)

        if request.password != request.password_confirmation:
            raise ValueError("Пароли не совпадают")

        if not request.is_adult_confirmed:
            raise ValueError("Регистрация доступна только пользователям старше 18 лет")

        if not request.user_agreement.accepted:
            raise ValueError("Нужно принять Пользовательское соглашение")

        if not request.personal_data_consent.accepted:
            raise ValueError("Нужно дать согласие на обработку персональных данных")

        legal_service.require_current_version("user_agreement", request.user_agreement.version)
        legal_service.require_current_version(
            "personal_data_consent",
            request.personal_data_consent.version,
        )
        legal_service.require_current_version("privacy_policy", request.privacy_policy_version)

        marketing = request.marketing_consent or MarketingConsentRequest(
            version=legal_service.require_current_version(
                "marketing_consent",
                legal_service.get_active_document("marketing_consent").version,
            ).version,
        )
        legal_service.require_current_version("marketing_consent", marketing.version)

        existing = self.db.scalar(
            select(AuthAccount).where(func.lower(AuthAccount.login) == login)
        )

        if existing is not None:
            raise ValueError("Пользователь с таким логином уже существует")

        email = self.validate_email(request.email)
        phone = self.normalize_phone(request.phone)
        if phone is None:
            raise ValueError("Телефон обязателен для регистрации")
        display_name = request.display_name.strip()

        if len(display_name) < 2:
            raise ValueError("Имя должно быть не короче 2 символов")

        role = self.db.scalar(select(Role).where(Role.code == RoleCode.USER.value))

        if role is None:
            raise ValueError("Role user not found")

        user = User(
            display_name=display_name,
            phone=phone,
            phone_verified=False,
            email=email,
        )
        self.db.add(user)
        self.db.flush()

        self.db.add(
            AuthAccount(
                user_id=user.id,
                login=login,
                password_hash=self.hash_password(request.password),
            )
        )
        self.db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=None))

        common_meta = {
            "ip_address": ip_address,
            "user_agent": user_agent,
            "source": source,
        }
        self.db.add_all(
            [
                UserConsent(
                    user_id=user.id,
                    document_code="user_agreement",
                    document_version=request.user_agreement.version,
                    status=ConsentStatus.ACCEPTED.value,
                    accepted_at=now,
                    consent_payload={"accepted": True, "is_adult_confirmed": True},
                    **common_meta,
                ),
                UserConsent(
                    user_id=user.id,
                    document_code="personal_data_consent",
                    document_version=request.personal_data_consent.version,
                    status=ConsentStatus.ACCEPTED.value,
                    accepted_at=now,
                    consent_payload={
                        "accepted": True,
                        "privacy_policy_version": request.privacy_policy_version,
                    },
                    **common_meta,
                ),
                UserConsent(
                    user_id=user.id,
                    document_code="privacy_policy",
                    document_version=request.privacy_policy_version,
                    status=ConsentStatus.ACCEPTED.value,
                    accepted_at=now,
                    consent_payload={"acknowledged": True},
                    **common_meta,
                ),
                UserConsent(
                    user_id=user.id,
                    document_code="marketing_consent",
                    document_version=marketing.version,
                    status=ConsentStatus.ACCEPTED.value,
                    accepted_at=now,
                    consent_payload={
                        "channels": {
                            "email": marketing.email,
                            "telegram": marketing.telegram,
                            "max": marketing.max,
                        }
                    },
                    **common_meta,
                ),
            ]
        )

        self.db.commit()
        self.db.refresh(user)
        return user

    def create_auth_user(
        self,
        login: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        self.ensure_initial_roles()
        normalized_login = self.normalize_login(login)
        user = User(display_name=display_name or normalized_login)
        self.db.add(user)
        self.db.flush()
        self.db.add(
            AuthAccount(
                user_id=user.id,
                login=normalized_login,
                password_hash=self.hash_password(password),
            )
        )
        self.assign_role(user.id, RoleCode.USER.value, assigned_by_user_id=None)
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(
        self,
        user: User,
        *,
        current_password: str,
        new_password: str,
        new_password_confirmation: str,
    ) -> None:
        auth_account = next(
            (account for account in user.auth_accounts if account.is_active),
            None,
        )

        if auth_account is None:
            raise ValueError("Для этого аккаунта не настроен вход по паролю")

        if not self.verify_password(current_password, auth_account.password_hash):
            raise ValueError("Текущий пароль указан неверно")

        if new_password != new_password_confirmation:
            raise ValueError("Новые пароли не совпадают")

        auth_account.password_hash = self.hash_password(new_password)
        self.db.commit()

    def update_marketing_consent(
        self,
        user: User,
        request: MarketingConsentRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
        source: str = ConsentSource.WEB.value,
    ) -> UserConsent:
        LegalDocumentService().require_current_version("marketing_consent", request.version)
        now = utc_now()
        latest = self.db.scalar(
            select(UserConsent)
            .where(
                UserConsent.user_id == user.id,
                UserConsent.document_code == "marketing_consent",
                UserConsent.status == ConsentStatus.ACCEPTED.value,
            )
            .order_by(UserConsent.created_at.desc())
        )

        if latest is not None:
            latest.status = ConsentStatus.REVOKED.value
            latest.revoked_at = now

        consent = UserConsent(
            user_id=user.id,
            document_code="marketing_consent",
            document_version=request.version,
            status=ConsentStatus.ACCEPTED.value,
            accepted_at=now,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_payload={
                "channels": {
                    "email": request.email,
                    "telegram": request.telegram,
                    "max": request.max,
                }
            },
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def assign_role(
        self,
        user_id: UUID,
        role_code: str,
        assigned_by_user_id: UUID | None,
    ) -> UserRole:
        role = self.db.scalar(select(Role).where(Role.code == role_code))

        if role is None:
            raise ValueError("Role not found")

        user = self.db.get(User, user_id)

        if user is None:
            raise ValueError("User not found")

        existing = self.db.get(UserRole, {"user_id": user_id, "role_id": role.id})

        if existing is not None:
            return existing

        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            assigned_by_user_id=assigned_by_user_id,
        )
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role

    def remove_role(self, user_id: UUID, role_code: str) -> None:
        role = self.db.scalar(select(Role).where(Role.code == role_code))

        if role is None:
            raise ValueError("Role not found")

        user_role = self.db.get(UserRole, {"user_id": user_id, "role_id": role.id})

        if user_role is None:
            raise ValueError("Role is not assigned")

        if role_code == RoleCode.SUPER_ADMIN.value:
            remaining_super_admins = self.db.scalars(
                select(UserRole)
                .join(User, User.id == UserRole.user_id)
                .where(
                    UserRole.role_id == role.id,
                    UserRole.user_id != user_id,
                    User.is_active.is_(True),
                )
            ).all()

            if not remaining_super_admins:
                raise ValueError("Cannot remove the last super_admin")

        self.db.delete(user_role)
        self.db.commit()

    def link_messenger_account_to_user_by_verified_phone(self, phone: str) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.phone == phone,
                User.phone_verified.is_(True),
            )
        )
