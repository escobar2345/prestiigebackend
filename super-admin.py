"""
create_super_admin.py
─────────────────────
Run this script ONCE to create your first super_admin account.
This is done manually so that no regular user can ever become a super_admin
through the normal registration form.

Usage:
    python create_super_admin.py
"""

from database import SessionLocal, engine, Base
from models import User, UserRole
import bcrypt as bcrypt_lib

# Create tables if they don't exist yet
Base.metadata.create_all(bind=engine)


def create_super_admin(username: str, email: str, password: str):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            print(f"⚠️  User '{username}' already exists with role: {existing.role}")
            return

        # Hash the password
        hashed = bcrypt_lib.hashpw(password.encode('utf-8'), bcrypt_lib.gensalt()).decode('utf-8')

        # Create the super_admin user
        admin = User(
            username=username,
            email=email,
            password=hashed,
            role=UserRole.super_admin  # ← This is the key line
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"✅ Super admin created successfully!")
        print(f"   Username : {admin.username}")
        print(f"   Email    : {admin.email}")
        print(f"   Role     : {admin.role}")
        print(f"\n🔐 You can now login at: http://localhost:8000/auth/login-page")

    finally:
        db.close()


if __name__ == "__main__":
    # ── CHANGE THESE VALUES ──────────────────────────────────
    ADMIN_USERNAME = "superadmin"
    ADMIN_EMAIL    = "admin@yourstore.com"
    ADMIN_PASSWORD = "StrongPassword123!"  # Use a strong password!
    # ─────────────────────────────────────────────────────────

    create_super_admin(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)