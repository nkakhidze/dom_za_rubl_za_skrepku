from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin_access
from app.db.models.item import Item, ItemStatus
from app.schemas.item import AdminItemCreateRequest, AdminItemResponse, AdminItemUpdateRequest

router = APIRouter(
    prefix="/admin/items",
    tags=["admin items"],
    dependencies=[Depends(require_admin_access)],
)

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


@router.get("", response_model=list[AdminItemResponse])
def get_items(
    db: Session = Depends(get_db),
    is_current: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Item).order_by(Item.sequence_number.asc().nullslast(), Item.created_at.desc())

    if is_current is not None:
        query = query.where(Item.is_current == is_current)

    if is_public is not None:
        query = query.where(Item.is_public == is_public)

    return db.scalars(query.limit(limit).offset(offset)).all()


@router.post("", response_model=AdminItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    request: AdminItemCreateRequest,
    db: Session = Depends(get_db),
):
    if request.is_current:
        db.query(Item).filter(Item.is_current.is_(True)).update(
            {Item.is_current: False, Item.status: ItemStatus.PAST.value},
            synchronize_session=False,
        )

    next_sequence_number = request.sequence_number

    if request.is_current and next_sequence_number is None:
        max_sequence_number = db.scalar(select(func.max(Item.sequence_number)))
        next_sequence_number = (max_sequence_number or 0) + 1

    item = Item(
        title=request.title,
        description=request.description,
        item_type=request.item_type.value,
        internal_value=request.internal_value,
        valuation_source=request.valuation_source,
        owner_type=request.owner_type.value,
        owner_name=request.owner_name,
        status=ItemStatus.CURRENT.value if request.is_current else ItemStatus.PLANNED.value,
        sequence_number=next_sequence_number,
        is_current=request.is_current,
        is_public=request.is_public,
        public_story=request.public_story,
        photo_url=request.photo_url,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.patch("/{item_id}", response_model=AdminItemResponse)
def update_item(
    item_id: UUID,
    request: AdminItemUpdateRequest,
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )

    update_data = request.model_dump(exclude_unset=True)

    if update_data.get("is_current") is True:
        db.query(Item).filter(Item.id != item_id, Item.is_current.is_(True)).update(
            {Item.is_current: False, Item.status: ItemStatus.PAST.value},
            synchronize_session=False,
        )
        item.status = ItemStatus.CURRENT.value

        if item.sequence_number is None and update_data.get("sequence_number") is None:
            max_sequence_number = db.scalar(select(func.max(Item.sequence_number)))
            item.sequence_number = (max_sequence_number or 0) + 1

    for field_name, field_value in update_data.items():
        if field_name == "item_type" and field_value is not None:
            item.item_type = field_value.value
        elif field_name == "owner_type" and field_value is not None:
            item.owner_type = field_value.value
        elif field_name == "is_current":
            item.is_current = field_value
        else:
            setattr(item, field_name, field_value)

    db.commit()
    db.refresh(item)

    return item
