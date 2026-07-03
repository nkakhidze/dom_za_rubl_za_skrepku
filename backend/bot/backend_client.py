from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class BackendClientError(RuntimeError):
    pass


class BackendUnavailableError(BackendClientError):
    pass


class BackendUnauthorizedError(BackendClientError):
    pass


class BackendValidationError(BackendClientError):
    pass


class BackendConflictError(BackendClientError):
    pass


class BackendLinkExpiredError(BackendClientError):
    pass


class BackendUnexpectedError(BackendClientError):
    pass


@dataclass(frozen=True)
class TelegramUserData:
    telegram_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


class TelegramBackendClient:
    def __init__(
        self,
        base_url: str,
        internal_token: str,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.internal_token = internal_token
        self._client = client

    async def __aenter__(self) -> "TelegramBackendClient":
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=5.0, read=20.0),
                headers={
                    "Authorization": f"Bearer {self.internal_token}",
                    "User-Agent": "paperclip-telegram-bot/1.0",
                },
            )

        return self

    async def __aexit__(self, *args) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("TelegramBackendClient must be used as an async context manager")

        return self._client

    async def resolve_user(self, user: TelegramUserData) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/api/internal/telegram/users/resolve",
            json=self._telegram_user_payload(user),
        )
        return response

    async def get_user_offers(self, telegram_user_id: str) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            "/api/internal/telegram/offers",
            params={"telegram_user_id": telegram_user_id},
        )
        return response

    async def consume_account_link(
        self,
        *,
        token: str,
        user: TelegramUserData,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/api/internal/telegram/account-links/consume",
            json={
                "token": token,
                **self._telegram_user_payload(user),
            },
        )
        return response

    async def consume_login_link(
        self,
        *,
        token: str,
        user: TelegramUserData,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/api/internal/telegram/login-links/consume",
            json={
                "token": token,
                **self._telegram_user_payload(user),
            },
        )
        return response

    async def create_offer(
        self,
        *,
        user: TelegramUserData,
        title: str,
        description: str,
        city: str | None,
        declared_value: int | None,
        participant_public_name: str | None,
        participant_visible: bool,
        idempotency_key: str,
        photos: list[bytes],
    ) -> dict[str, Any]:
        data = {
            "telegram_user_id": user.telegram_user_id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "language_code": user.language_code or "",
            "title": title,
            "description": description,
            "city": city or "",
            "declared_value": "" if declared_value is None else str(declared_value),
            "exchange_preference": "any_offer",
            "participant_public_name": participant_public_name or "",
            "participant_visible": "true" if participant_visible else "false",
            "idempotency_key": idempotency_key,
        }
        files = [
            ("photos", (f"telegram-photo-{index}.jpg", content, "image/jpeg"))
            for index, content in enumerate(photos, start=1)
        ]
        return await self._request(
            "POST",
            "/api/internal/telegram/offers",
            data=data,
            files=files,
        )

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Authorization", f"Bearer {self.internal_token}")
        headers.setdefault("User-Agent", "paperclip-telegram-bot/1.0")
        url = f"{self.base_url}{path}"

        try:
            response = await self.client.request(
                method,
                url,
                headers=headers,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise BackendUnavailableError(
                f"Backend unavailable: {method} {url}: {exc}"
            ) from exc

        if response.is_success:
            return response.json()

        if response.status_code in {401, 403}:
            raise BackendUnauthorizedError(
                f"Backend rejected internal token for {method} {path}"
            )
        if response.status_code == 409:
            raise BackendConflictError(self._detail(response))
        if response.status_code == 410:
            raise BackendLinkExpiredError(self._detail(response))
        if response.status_code in {400, 422, 429}:
            raise BackendValidationError(self._detail(response))

        raise BackendUnexpectedError(f"Backend returned {response.status_code}")

    @staticmethod
    def _telegram_user_payload(user: TelegramUserData) -> dict[str, Any]:
        return {
            "telegram_user_id": user.telegram_user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
        }

    @staticmethod
    def _detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text

        detail = payload.get("detail", payload)
        if isinstance(detail, list):
            return "; ".join(str(item.get("msg", item)) for item in detail)
        return str(detail)


BackendClient = TelegramBackendClient
