from typing import Any

import httpx


class BackendClientError(RuntimeError):
    pass


class BackendClient:
    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._client = client

    async def __aenter__(self) -> "BackendClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20)

        return self

    async def __aexit__(self, *args) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("BackendClient must be used as an async context manager")

        return self._client

    async def create_or_get_user_by_telegram_id(
        self,
        telegram_id: str,
        display_name: str | None,
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/api/users/telegram",
            json={
                "telegram_id": telegram_id,
                "display_name": display_name,
            },
        )

        return self._json_or_raise(response)

    async def upload_image(
        self,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/api/files/images",
            files={
                "file": (
                    filename,
                    content,
                    content_type,
                )
            },
        )

        return self._json_or_raise(response)

    async def create_offer(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/api/offers",
            json=payload,
        )

        return self._json_or_raise(response)

    async def get_my_offers(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.base_url}/api/users/{user_id}/offers",
        )

        return self._json_or_raise(response)

    async def create_item(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/api/items",
            json=payload,
        )

        return self._json_or_raise(response)

    async def get_user_items(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.base_url}/api/users/{user_id}/items",
        )

        return self._json_or_raise(response)

    async def create_deal(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/api/deals",
            json=payload,
        )

        return self._json_or_raise(response)

    async def get_user_deals(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.base_url}/api/users/{user_id}/deals",
        )

        return self._json_or_raise(response)

    def _json_or_raise(self, response: httpx.Response):
        if response.is_success:
            return response.json()

        raise BackendClientError(
            f"Backend returned {response.status_code}: {response.text}"
        )
