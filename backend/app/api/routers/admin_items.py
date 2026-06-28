from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_admin_access, require_any_role
from app.db.models.auth import RoleCode
from app.db.models.deal import Deal
from app.db.models.item import Item, ItemStatus
from app.db.models.item_photo import ItemPhoto
from app.schemas.item import (
    AdminItemCreateRequest,
    AdminItemPhotoCreateRequest,
    AdminItemPhotoResponse,
    AdminItemResponse,
    AdminItemUpdateRequest,
)

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
    received_deal_date = (
        select(Deal.deal_date)
        .where(Deal.received_item_id == Item.id)
        .order_by(Deal.deal_date.desc())
        .limit(1)
        .scalar_subquery()
    )

    query = (
        select(Item)
        .options(selectinload(Item.photos))
        .order_by(
            Item.is_current.desc(),
            received_deal_date.desc().nullslast(),
            Item.sequence_number.desc().nullslast(),
            Item.created_at.desc(),
        )
    )

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
        vk_url=request.vk_url,
        tiktok_url=request.tiktok_url,
        youtube_url=request.youtube_url,
        dzen_url=request.dzen_url,
        rutube_url=request.rutube_url,
        instagram_url=request.instagram_url,
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


@router.post(
    "/{item_id}/photos",
    response_model=AdminItemPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role(RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def add_item_photo(
    item_id: UUID,
    request: AdminItemPhotoCreateRequest,
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )

    photo = ItemPhoto(
        item_id=item.id,
        photo_url=request.photo_url,
        sort_order=request.sort_order,
    )

    if item.photo_url is None:
        item.photo_url = request.photo_url

    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


@router.delete(
    "/{item_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_any_role(RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def delete_item_photo(
    item_id: UUID,
    photo_id: UUID,
    db: Session = Depends(get_db),
):
    photo = db.scalar(
        select(ItemPhoto).where(
            ItemPhoto.id == photo_id,
            ItemPhoto.item_id == item_id,
        )
    )

    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фото не найдено",
        )

    db.delete(photo)
    db.commit()
