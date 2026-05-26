from collections.abc import Generator
from typing import Annotated
import secrets

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def require_admin_access(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token is required",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )
