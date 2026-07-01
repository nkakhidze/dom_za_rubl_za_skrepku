from dataclasses import dataclass
from io import BytesIO
import logging
from pathlib import Path
from urllib.parse import urlparse
import uuid

from fastapi import UploadFile, status
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

from app.core.config import settings


logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
OUTPUT_MIME_TYPE = "image/webp"


class ImageUploadError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class SavedImage:
    image_url: str
    thumbnail_url: str
    filename: str
    thumbnail_filename: str
    width: int
    height: int
    thumbnail_width: int
    thumbnail_height: int
    size_bytes: int
    thumbnail_size_bytes: int
    mime_type: str = OUTPUT_MIME_TYPE

    @property
    def photo_url(self) -> str:
        return self.image_url


def _has_transparency(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA"}:
        return True

    if image.mode == "P" and "transparency" in image.info:
        return True

    return False


def _prepare_for_webp(image: Image.Image) -> Image.Image:
    if _has_transparency(image):
        return image.convert("RGBA")

    return image.convert("RGB")


def _resized_copy(image: Image.Image, max_size: int) -> Image.Image:
    resized = image.copy()
    resized.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return resized


def _save_webp(image: Image.Image, output_path: Path, *, quality: int) -> None:
    image.save(
        output_path,
        format="WEBP",
        quality=quality,
        method=settings.image_webp_method,
    )


def _url_for(filename: str) -> str:
    return f"{settings.public_base_url}/uploads/images/{filename}"


async def save_optimized_image(upload: UploadFile, output_dir: Path) -> SavedImage:
    Image.MAX_IMAGE_PIXELS = settings.image_max_dimension * settings.image_max_dimension
    ImageFile.LOAD_TRUNCATED_IMAGES = False

    output_dir.mkdir(parents=True, exist_ok=True)
    max_size_bytes = settings.image_max_file_size_mb * 1024 * 1024
    content = await upload.read()

    if len(content) > max_size_bytes:
        raise ImageUploadError(
            f"Размер изображения не должен превышать {settings.image_max_file_size_mb} МБ.",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    base_name = str(uuid.uuid4())
    filename = f"{base_name}.webp"
    thumbnail_filename = f"{base_name}_thumb.webp"
    image_path = output_dir / filename
    thumbnail_path = output_dir / thumbnail_filename
    created_paths = [image_path, thumbnail_path]

    try:
        try:
            with Image.open(BytesIO(content)) as opened_image:
                image_format = opened_image.format

                if image_format not in SUPPORTED_IMAGE_FORMATS:
                    raise ImageUploadError(
                        "Поддерживаются только JPEG, PNG и WebP.",
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )

                width, height = opened_image.size
                if (
                    width > settings.image_max_dimension
                    or height > settings.image_max_dimension
                ):
                    raise ImageUploadError(
                        f"Максимальное разрешение изображения — {settings.image_max_dimension} × {settings.image_max_dimension} пикселей.",
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

                image = ImageOps.exif_transpose(opened_image)
                image.load()
        except ImageUploadError:
            raise
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as error:
            raise ImageUploadError(
                "Не удалось прочитать изображение. Возможно, файл повреждён.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from error

        prepared_image = _prepare_for_webp(image)
        main_image = _resized_copy(prepared_image, settings.image_main_max_size)
        thumbnail_image = _resized_copy(prepared_image, settings.image_thumb_max_size)

        _save_webp(main_image, image_path, quality=settings.image_main_quality)
        _save_webp(thumbnail_image, thumbnail_path, quality=settings.image_thumb_quality)

        return SavedImage(
            image_url=_url_for(filename),
            thumbnail_url=_url_for(thumbnail_filename),
            filename=filename,
            thumbnail_filename=thumbnail_filename,
            width=main_image.width,
            height=main_image.height,
            thumbnail_width=thumbnail_image.width,
            thumbnail_height=thumbnail_image.height,
            size_bytes=image_path.stat().st_size,
            thumbnail_size_bytes=thumbnail_path.stat().st_size,
        )
    except ImageUploadError:
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise
    except OSError as error:
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise ImageUploadError(
            "Не удалось сохранить изображение.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from error


def _local_upload_path_from_url(file_url: str) -> Path | None:
    parsed_url = urlparse(file_url)
    public_base = urlparse(settings.public_base_url)

    if parsed_url.scheme and (
        parsed_url.scheme != public_base.scheme or parsed_url.netloc != public_base.netloc
    ):
        return None

    marker = "/uploads/images/"
    if marker not in parsed_url.path:
        return None

    filename = Path(parsed_url.path.rsplit(marker, 1)[1]).name
    if not filename:
        return None

    return Path(settings.upload_dir) / "images" / filename


def delete_uploaded_image_files(*file_urls: str | None) -> None:
    for file_url in file_urls:
        if not file_url:
            continue

        path = _local_upload_path_from_url(file_url)
        if path is None:
            continue

        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to delete uploaded image file", exc_info=True)
