from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.db.models.offer_photo import OfferPhoto
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
    )

    Base.metadata.create_all(engine)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "public_base_url", "http://testserver")
    monkeypatch.setattr(settings, "image_max_file_size_mb", 15)
    monkeypatch.setattr(settings, "image_max_dimension", 10000)
    monkeypatch.setattr(settings, "image_main_max_size", 1920)
    monkeypatch.setattr(settings, "image_thumb_max_size", 640)

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


def make_image_bytes(
    *,
    fmt: str = "JPEG",
    size: tuple[int, int] = (900, 600),
    mode: str = "RGB",
) -> bytes:
    color = (220, 10, 10, 128) if mode in {"RGBA", "CMYK"} else (220, 10, 10)
    image = Image.new(mode, size, color)
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def upload_image(client: TestClient, content: bytes, filename: str = "photo.jpg"):
    return client.post(
        "/api/files/images",
        files={"file": (filename, content, "application/octet-stream")},
    )


def local_path(url: str, upload_root: str) -> Path:
    filename = url.rsplit("/", 1)[1]
    return Path(upload_root) / "images" / filename


@pytest.mark.parametrize(
    ("fmt", "filename"),
    [
        ("JPEG", "source.jpg"),
        ("PNG", "source.png"),
        ("WEBP", "source.webp"),
    ],
)
def test_image_upload_converts_supported_formats_to_webp(client, fmt, filename):
    response = upload_image(client, make_image_bytes(fmt=fmt), filename)

    assert response.status_code == 201
    payload = response.json()
    assert payload["image_url"] == payload["photo_url"]
    assert payload["image_url"].endswith(".webp")
    assert payload["thumbnail_url"].endswith("_thumb.webp")
    assert payload["mime_type"] == "image/webp"
    assert payload["width"] == 900
    assert payload["height"] == 600
    assert payload["thumbnail_width"] == 640
    assert payload["thumbnail_height"] == 427
    assert payload["size_bytes"] > 0
    assert payload["thumbnail_size_bytes"] > 0

    image_path = local_path(payload["image_url"], settings.upload_dir)
    thumb_path = local_path(payload["thumbnail_url"], settings.upload_dir)
    assert image_path.exists()
    assert thumb_path.exists()
    assert filename not in image_path.name

    with Image.open(image_path) as image:
        assert image.format == "WEBP"


def test_large_image_is_resized_and_small_image_is_not_upscaled(client):
    large_response = upload_image(client, make_image_bytes(size=(3000, 2000)))
    small_response = upload_image(client, make_image_bytes(size=(320, 240)))

    assert large_response.status_code == 201
    assert max(large_response.json()["width"], large_response.json()["height"]) == 1920
    assert max(large_response.json()["thumbnail_width"], large_response.json()["thumbnail_height"]) == 640

    assert small_response.status_code == 201
    assert small_response.json()["width"] == 320
    assert small_response.json()["height"] == 240
    assert small_response.json()["thumbnail_width"] == 320
    assert small_response.json()["thumbnail_height"] == 240


def test_transparent_png_and_cmyk_jpeg_are_processed(client):
    png_response = upload_image(client, make_image_bytes(fmt="PNG", mode="RGBA"), "transparent.png")
    cmyk_response = upload_image(client, make_image_bytes(fmt="JPEG", mode="CMYK"), "cmyk.jpg")

    assert png_response.status_code == 201
    assert cmyk_response.status_code == 201


def test_invalid_images_and_limits_return_readable_errors(client, monkeypatch):
    broken_response = upload_image(client, b"not an image", "fake.jpg")
    assert broken_response.status_code == 422
    assert "Не удалось прочитать изображение" in broken_response.json()["detail"]

    monkeypatch.setattr(settings, "image_max_file_size_mb", 0)
    too_large_response = upload_image(client, make_image_bytes(), "large.jpg")
    assert too_large_response.status_code == 413
    assert "Размер изображения" in too_large_response.json()["detail"]

    monkeypatch.setattr(settings, "image_max_file_size_mb", 15)
    monkeypatch.setattr(settings, "image_max_dimension", 100)
    too_wide_response = upload_image(client, make_image_bytes(size=(120, 80)), "wide.jpg")
    assert too_wide_response.status_code == 422
    assert "Максимальное разрешение" in too_wide_response.json()["detail"]


def test_unsupported_real_image_format_returns_415(client):
    response = upload_image(client, make_image_bytes(fmt="GIF"), "animated.gif")

    assert response.status_code == 415
    assert "JPEG, PNG и WebP" in response.json()["detail"]


def test_offer_creation_persists_thumbnail_metadata(client):
    upload_response = upload_image(client, make_image_bytes(), "offer.jpg")
    image = upload_response.json()

    create_response = client.post(
        "/api/offers",
        json={
            "messenger_type": "web",
            "external_user_id": "image-meta-user",
            "title": "Image meta offer",
            "description": "Offer with optimized image metadata.",
            "offer_type": "physical_item",
            "city": "Tomsk",
            "declared_value": 100,
            "photo_urls": [image["photo_url"]],
            "photo_thumbnail_urls": [image["thumbnail_url"]],
            "photo_widths": [image["width"]],
            "photo_heights": [image["height"]],
            "photo_thumbnail_widths": [image["thumbnail_width"]],
            "photo_thumbnail_heights": [image["thumbnail_height"]],
            "photo_size_bytes": [image["size_bytes"]],
            "photo_thumbnail_size_bytes": [image["thumbnail_size_bytes"]],
            "exchange_preference": "any_offer",
            "consent_accepted": True,
            "participant_visible": False,
        },
    )

    assert create_response.status_code == 201
    offer_id = UUID(create_response.json()["id"])

    with next(app.dependency_overrides[get_db]()) as db:
        photo = db.scalar(select(OfferPhoto).where(OfferPhoto.offer_id == offer_id))

    assert photo is not None
    assert photo.thumbnail_url == image["thumbnail_url"]
    assert photo.width == image["width"]
    assert photo.thumbnail_width == image["thumbnail_width"]
