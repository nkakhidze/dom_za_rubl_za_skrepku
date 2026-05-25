from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.file import ImageUploadResponse
from app.services.file_storage_service import FileStorageService

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
        photo_url, filename = await service.save_image(file)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return ImageUploadResponse(
        photo_url=photo_url,
        filename=filename,
    )