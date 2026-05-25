from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.item import Item
from app.schemas.item import AdminItemCreateRequest, AdminItemResponse

router = APIRouter(
    prefix="/admin/items",
    tags=["admin items"],
)


@router.post("", response_model=AdminItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    request: AdminItemCreateRequest,
    db: Session = Depends(get_db),
):
    if request.is_current:
        db.query(Item).filter(Item.is_current.is_(True)).update(
            {Item.is_current: False},
            synchronize_session=False,
        )

    item = Item(
        title=request.title,
        description=request.description,
        item_type=request.item_type.value,
        internal_value=request.internal_value,
        valuation_source=request.valuation_source,
        owner_type=request.owner_type.value,
        owner_name=request.owner_name,
        is_current=request.is_current,
        is_public=request.is_public,
        public_story=request.public_story,
        photo_url=request.photo_url,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get("", response_model=list[AdminItemResponse])
def get_items(
    db: Session = Depends(get_db),
    is_current: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Item).order_by(Item.created_at.desc())

    if is_current is not None:
        query = query.where(Item.is_current == is_current)

    if is_public is not None:
        query = query.where(Item.is_public == is_public)

    return db.scalars(query.limit(limit).offset(offset)).all()


@router.get("/{item_id}", response_model=AdminItemResponse)
def get_item(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )

    return item