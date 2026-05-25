import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class FileStorageService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.images_dir = self.upload_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    async def save_image(self, file: UploadFile) -> tuple[str, str]:
        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValueError("Можно загружать только изображения JPG, PNG или WEBP")

        extension = ALLOWED_IMAGE_CONTENT_TYPES[file.content_type]
        filename = f"{uuid.uuid4()}{extension}"
        file_path = self.images_dir / filename

        content = await file.read()

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

        if len(content) > max_size_bytes:
            raise ValueError(
                f"Размер файла не должен превышать {settings.max_upload_size_mb} МБ"
            )

        file_path.write_bytes(content)

        photo_url = f"{settings.public_base_url}/uploads/images/{filename}"

        return photo_url, filename