import unittest

import httpx

from bot.backend_client import BackendClient, BackendClientError


class BackendClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_create_or_get_user_by_telegram_id_sends_expected_request(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "id": "user-id",
                    "telegram_id": "123",
                    "display_name": "Nick",
                },
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with BackendClient("http://backend", async_client) as backend:
            response = await backend.create_or_get_user_by_telegram_id("123", "Nick")

        self.assertEqual(response["id"], "user-id")
        self.assertEqual(requests[0].method, "POST")
        self.assertEqual(str(requests[0].url), "http://backend/api/users/telegram")
        self.assertEqual(
            requests[0].read(),
            b'{"telegram_id":"123","display_name":"Nick"}',
        )

    async def test_create_offer_sends_payload(self):
        requests: list[httpx.Request] = []
        payload = {
            "messenger_type": "telegram",
            "external_user_id": "123",
            "title": "Offer",
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(201, json={"id": "offer-id", "status": "new"})

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with BackendClient("http://backend", async_client) as backend:
            response = await backend.create_offer(payload)

        self.assertEqual(response["id"], "offer-id")
        self.assertEqual(str(requests[0].url), "http://backend/api/offers")
        self.assertEqual(
            requests[0].read(),
            b'{"messenger_type":"telegram","external_user_id":"123","title":"Offer"}',
        )

    async def test_upload_image_sends_multipart_file(self):
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            body = request.read()
            self.assertIn(b"offer.jpg", body)
            self.assertIn(b"image/jpeg", body)
            self.assertIn(b"image-bytes", body)
            return httpx.Response(
                201,
                json={
                    "photo_url": "http://backend/uploads/images/offer.jpg",
                    "filename": "offer.jpg",
                },
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with BackendClient("http://backend", async_client) as backend:
            response = await backend.upload_image(
                content=b"image-bytes",
                filename="offer.jpg",
                content_type="image/jpeg",
            )

        self.assertEqual(
            response["photo_url"],
            "http://backend/uploads/images/offer.jpg",
        )
        self.assertEqual(str(requests[0].url), "http://backend/api/files/images")

    async def test_backend_error_raises_client_error(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"detail": "Invalid request"})

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with BackendClient("http://backend", async_client) as backend:
            with self.assertRaises(BackendClientError):
                await backend.create_offer({"title": "Broken"})
