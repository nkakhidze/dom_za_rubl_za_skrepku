from collections.abc import Callable, Generator
import logging
import secrets
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models.auth import RoleCode
from app.db.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWT Bearer")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required",
        )

    return credentials.credentials.strip()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer_token(credentials)
    return _get_user_from_jwt_token(token, db)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None

    token = _extract_bearer_token(credentials)
    return _get_user_from_jwt_token(token, db)


def _get_user_from_jwt_token(token: str, db: Session) -> User:
    payload = AuthService(db).decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from None

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
        )

    return user


def _user_role_codes(user: User) -> set[str]:
    return {user_role.role.code for user_role in user.user_roles}


def require_any_role(*allowed_roles: str) -> Callable:
    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: Session = Depends(get_db),
    ) -> User | None:
        token = _extract_bearer_token(credentials)

        if settings.allow_admin_token_auth and secrets.compare_digest(token, settings.admin_api_token):
            logger.warning("ADMIN_API_TOKEN fallback was used for role-protected endpoint")
            return None

        current_user = _get_user_from_jwt_token(token, db)
        user_roles = _user_role_codes(current_user)

        if user_roles.isdisjoint(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        return current_user

    return dependency


def require_admin_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> None:
    token = _extract_bearer_token(credentials)

    if settings.allow_admin_token_auth and secrets.compare_digest(token, settings.admin_api_token):
        logger.warning("ADMIN_API_TOKEN fallback was used for admin endpoint")
        return

    user = _get_user_from_jwt_token(token, db)
    roles = _user_role_codes(user)
    allowed = {
        RoleCode.EDITOR.value,
        RoleCode.MODERATOR.value,
        RoleCode.ADMIN.value,
        RoleCode.SUPER_ADMIN.value,
    }

    if roles.isdisjoint(allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role",
        )


def require_telegram_internal_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    token = _extract_bearer_token(credentials)

    if not settings.telegram_internal_api_token or not secrets.compare_digest(
        token,
        settings.telegram_internal_api_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal token",
        )
