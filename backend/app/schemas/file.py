from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    photo_url: str
    filename: str