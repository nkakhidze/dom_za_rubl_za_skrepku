from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.item import Item
from app.schemas.item import PublicCurrentItemResponse

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


@router.get("/current-item", response_model=PublicCurrentItemResponse)
def get_current_item(
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(Item).where(
            Item.is_current.is_(True),
            Item.is_public.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Текущий предмет пока не опубликован",
        )

    return item


@router.get("/exchange-chain")
def get_exchange_chain():
    return []