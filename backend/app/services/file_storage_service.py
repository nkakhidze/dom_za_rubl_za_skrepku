from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.services.image_service import SavedImage, save_optimized_image


class FileStorageService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.images_dir = self.upload_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    async def save_image(self, file: UploadFile) -> SavedImage:
        return await save_optimized_image(file, self.images_dir)
