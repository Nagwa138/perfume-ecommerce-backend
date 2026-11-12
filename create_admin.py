"""
Interactive admin user seeder.
Prompts for username, password (hidden), and role — never prints the password.

Run with:  python create_admin.py
"""

import getpass
import sys

from sqlmodel import Session, select

from auth import hash_password
from models import AdminUser, engine


def main() -> None:
    print("=== AURA Perfume — Create Admin User ===")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    role = input("Role [admin/staff] (default: admin): ").strip().lower() or "admin"
    if role not in ("admin", "staff"):
        print("Role must be 'admin' or 'staff'.")
        sys.exit(1)

    with Session(engine) as session:
        existing = session.exec(select(AdminUser).where(AdminUser.username == username)).first()
        if existing:
            print(f"User '{username}' already exists.")
            sys.exit(1)

        user = AdminUser(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        session.commit()

    print(f"\nAdmin user '{username}' ({role}) created successfully.")


if __name__ == "__main__":
    main()
