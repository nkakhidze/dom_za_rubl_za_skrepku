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
    args = parser.parse_args()

    if not args.login or not args.password:
        raise SystemExit("Set INITIAL_ADMIN_LOGIN/INITIAL_ADMIN_PASSWORD or pass --login/--password")

    db = SessionLocal()

    try:
        service = AuthService(db)
        service.ensure_initial_roles()
        existing_auth = db.scalar(select(AuthAccount).where(AuthAccount.login == args.login))

        if existing_auth is None:
            user = service.create_auth_user(
                login=args.login,
                password=args.password,
                display_name=args.login,
            )
        else:
            user = existing_auth.user

        if RoleCode.SUPER_ADMIN.value not in service.get_user_roles(user):
            service.assign_role(user.id, RoleCode.SUPER_ADMIN.value, assigned_by_user_id=None)

        print(f"super_admin ready: {args.login}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
