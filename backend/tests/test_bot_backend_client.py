import unittest
from pathlib import Path

import httpx

from bot.backend_client import (
    BackendConflictError,
    BackendLinkExpiredError,
    BackendUnauthorizedError,
    BackendValidationError,
    TelegramBackendClient,
    TelegramUserData,
)


class TelegramBackendClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_user_uses_internal_endpoint_and_token(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"user_id": "user-id", "created": True, "telegram_connected": True},
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
            response = await backend.resolve_user(
                TelegramUserData(
                    telegram_user_id="123",
                    username="nick",
                    first_name="Nick",
                    language_code="ru",
                )
            )

        self.assertEqual(response["user_id"], "user-id")
        self.assertEqual(str(requests[0].url), "http://backend/api/internal/telegram/users/resolve")
        self.assertEqual(requests[0].headers["authorization"], "Bearer secret")
        self.assertEqual(
            requests[0].read(),
            b'{"telegram_user_id":"123","username":"nick","first_name":"Nick","last_name":null,"language_code":"ru"}',
        )

    async def test_create_offer_sends_multipart_to_internal_endpoint(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            body = request.read()
            self.assertIn(b"telegram-photo-1.jpg", body)
            self.assertIn(b"image-bytes", body)
            self.assertIn(b"idempotency-key", body)
            return httpx.Response(
                201,
                json={
                    "offer_id": "offer-id",
                    "status": "new",
                    "status_label": "Новая заявка",
                    "created_at": "2026-06-29T00:00:00Z",
                },
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
            response = await backend.create_offer(
                user=TelegramUserData(telegram_user_id="123"),
                title="Offer",
                description="Long enough description",
                city="Tomsk",
                declared_value=100,
                participant_public_name="Nick",
                participant_visible=True,
                idempotency_key="idempotency-key",
                photos=[b"image-bytes"],
            )

        self.assertEqual(response["offer_id"], "offer-id")
        self.assertEqual(str(requests[0].url), "http://backend/api/internal/telegram/offers")

    async def test_get_user_offers_uses_telegram_id(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=[{"id": "offer-id"}])

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
            response = await backend.get_user_offers("123")

        self.assertEqual(response[0]["id"], "offer-id")
        self.assertEqual(
            str(requests[0].url),
            "http://backend/api/internal/telegram/offers?telegram_user_id=123",
        )

    async def test_consume_account_link_sends_token_and_telegram_user(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"user_id": "user-id", "telegram_connected": True},
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
            response = await backend.consume_account_link(
                token="link-token",
                user=TelegramUserData(telegram_user_id="123", username="nick"),
            )

        self.assertTrue(response["telegram_connected"])
        self.assertEqual(
            str(requests[0].url),
            "http://backend/api/internal/telegram/account-links/consume",
        )
        self.assertIn(b'"token":"link-token"', requests[0].read())

    async def test_consume_login_link_sends_token_and_telegram_user(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"user_id": "user-id", "telegram_connected": True},
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
            response = await backend.consume_login_link(
                token="login-token",
                user=TelegramUserData(telegram_user_id="123", username="nick"),
            )

        self.assertTrue(response["telegram_connected"])
        self.assertEqual(
            str(requests[0].url),
            "http://backend/api/internal/telegram/login-links/consume",
        )
        self.assertIn(b'"token":"login-token"', requests[0].read())

    async def test_errors_are_mapped_to_domain_exceptions(self):
        cases = [
            (403, BackendUnauthorizedError),
            (409, BackendConflictError),
            (410, BackendLinkExpiredError),
            (422, BackendValidationError),
        ]

        for status_code, expected_error in cases:
            async def handler(request: httpx.Request, status_code=status_code) -> httpx.Response:
                return httpx.Response(status_code, json={"detail": "error"})

            async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

            async with TelegramBackendClient("http://backend", "secret", async_client) as backend:
                with self.assertRaises(expected_error):
                    await backend.resolve_user(TelegramUserData(telegram_user_id="123"))


class TelegramBotContractTestCase(unittest.TestCase):
    def test_bot_does_not_expose_legacy_item_deal_commands(self):
        root = Path(__file__).resolve().parents[1]
        checked_sources = [
            root / "bot" / "main.py",
            root / "bot" / "backend_client.py",
        ]
        forbidden_commands = ["/new_item", "/respond", "/my_deals"]

        for source_path in checked_sources:
            source = source_path.read_text(encoding="utf-8")
            for command in forbidden_commands:
                self.assertNotIn(command, source, f"{command} leaked into {source_path}")

    def test_readme_does_not_list_legacy_bot_commands_as_available(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("- `/new_item`", source)
        self.assertNotIn("- `/respond <offer_id>`", source)
        self.assertNotIn("- `/my_deals`", source)

    def test_bot_menu_uses_exchange_offer_language(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "bot" / "main.py").read_text(encoding="utf-8")

        self.assertIn('BTN_NEW_OFFER = "📎 Предложить обмен"', source)
        self.assertNotIn("Предложить предмет", source)
