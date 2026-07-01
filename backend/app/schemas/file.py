from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    image_url: str
    photo_url: str
    thumbnail_url: str
    filename: str
    width: int
    height: int
    thumbnail_width: int
    thumbnail_height: int
    size_bytes: int
    thumbnail_size_bytes: int
    mime_type: str
