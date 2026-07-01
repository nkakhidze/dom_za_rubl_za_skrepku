from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.item import Item, ItemStatus, ItemType, OwnerType
from app.db.models.user import User
from app.schemas.item import UserItemCreateRequest, UserItemResponse


router = APIRouter(
    prefix="/items",
    tags=["items"],
)


@router.post("", response_model=UserItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    request: UserItemCreateRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    item = Item(
        user_id=user.id,
        title=request.title,
        description=request.description,
        item_type=ItemType.PHYSICAL_ITEM.value,
        owner_type=OwnerType.PERSONAL.value,
        status=ItemStatus.ACTIVE.value,
        is_current=False,
        is_public=False,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item
