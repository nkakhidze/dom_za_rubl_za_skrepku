from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_any_role
from app.db.models.auth import RoleCode
from app.db.models.user import User
from app.schemas.auth import AdminUserDetail, AdminUserListItem, RoleUpdateRequest
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/admin/users",
    tags=["admin users"],
)


def _user_roles(user: User) -> list[str]:
    return sorted(user_role.role.code for user_role in user.user_roles)


def _user_list_item(user: User) -> AdminUserListItem:
    return AdminUserListItem(
        id=user.id,
        display_name=user.display_name,
        phone=user.phone,
        phone_verified=user.phone_verified,
        is_active=user.is_active,
        roles=_user_roles(user),
    )


def _user_detail(user: User) -> AdminUserDetail:
    return AdminUserDetail(
        **_user_list_item(user).model_dump(),
        messenger_accounts=[
            {
                "messenger_type": account.messenger_type,
                "external_user_id": account.external_user_id,
                "username": account.username,
                "first_name": account.first_name,
                "last_name": account.last_name,
            }
            for account in user.messenger_accounts
        ],
        auth_logins=[auth_account.login for auth_account in user.auth_accounts],
    )


@router.get(
    "",
    response_model=list[AdminUserListItem],
    dependencies=[Depends(require_any_role(RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def get_users(db: Session = Depends(get_db)):
    return [_user_list_item(user) for user in db.scalars(select(User).order_by(User.created_at.desc())).all()]


@router.get(
    "/{user_id}",
    response_model=AdminUserDetail,
    dependencies=[Depends(require_any_role(RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value))],
)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _user_detail(user)


@router.post("/{user_id}/roles", response_model=AdminUserDetail)
def assign_role(
    user_id: UUID,
    request: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_roles = set(_user_roles(current_user))
    role = request.role

    if role in {RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value}:
        if RoleCode.SUPER_ADMIN.value not in current_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can assign admin roles",
            )
    elif role in {RoleCode.MODERATOR.value, RoleCode.EDITOR.value}:
        if current_roles.isdisjoint({RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role cannot be assigned")

    try:
        AuthService(db).assign_role(user_id, role, current_user.id)
    except ValueError as error:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(error).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    return _user_detail(db.get(User, user_id))


@router.delete("/{user_id}/roles/{role}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role(
    user_id: UUID,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_roles = set(_user_roles(current_user))

    if role in {RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value}:
        if RoleCode.SUPER_ADMIN.value not in current_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can remove admin roles",
            )
    elif role in {RoleCode.MODERATOR.value, RoleCode.EDITOR.value}:
        if current_roles.isdisjoint({RoleCode.ADMIN.value, RoleCode.SUPER_ADMIN.value}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role cannot be removed")

    try:
        AuthService(db).remove_role(user_id, role)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
