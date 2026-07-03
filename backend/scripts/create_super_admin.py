import argparse
import os

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models.auth import AuthAccount, RoleCode
from app.services.auth_service import AuthService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default=os.environ.get("INITIAL_ADMIN_LOGIN"))
    parser.add_argument("--password", default=os.environ.get("INITIAL_ADMIN_PASSWORD"))
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset password for an existing auth account.",
    )
    args = parser.parse_args()

    if not args.login or not args.password:
        raise SystemExit("Set INITIAL_ADMIN_LOGIN/INITIAL_ADMIN_PASSWORD or pass --login/--password")

    db = SessionLocal()

    try:
        service = AuthService(db)
        service.ensure_initial_roles()
        login = service.normalize_login(args.login)
        existing_auth = db.scalar(select(AuthAccount).where(AuthAccount.login == login))

        if existing_auth is None:
            user = service.create_auth_user(
                login=login,
                password=args.password,
                display_name=login,
            )
        else:
            user = existing_auth.user
            user.is_active = True
            existing_auth.is_active = True
            if args.reset_password:
                existing_auth.password_hash = service.hash_password(args.password)

        if RoleCode.SUPER_ADMIN.value not in service.get_user_roles(user):
            service.assign_role(user.id, RoleCode.SUPER_ADMIN.value, assigned_by_user_id=None)

        db.commit()
        print(f"super_admin ready: {login}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
