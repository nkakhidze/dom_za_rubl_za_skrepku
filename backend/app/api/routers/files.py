from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.file import ImageUploadResponse
from app.services.file_storage_service import FileStorageService
from app.services.image_service import ImageUploadError

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


@router.post(
    "/images",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    file: UploadFile = File(...),
):
    service = FileStorageService()

    try:
        saved_image = await service.save_image(file)
    except ImageUploadError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.message,
        ) from error

    return ImageUploadResponse(
        image_url=saved_image.image_url,
        photo_url=saved_image.photo_url,
        thumbnail_url=saved_image.thumbnail_url,
        filename=saved_image.filename,
        width=saved_image.width,
        height=saved_image.height,
        thumbnail_width=saved_image.thumbnail_width,
        thumbnail_height=saved_image.thumbnail_height,
        size_bytes=saved_image.size_bytes,
        thumbnail_size_bytes=saved_image.thumbnail_size_bytes,
        mime_type=saved_image.mime_type,
    )
