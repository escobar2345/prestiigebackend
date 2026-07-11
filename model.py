from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
import enum
from database import Base


# ─── Role Enum ────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    user        = "user"        # Regular customer — NO admin access
    super_admin = "super_admin" # Full admin access


# ─── User Table ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String, unique=True, nullable=False, index=True)
    email      = Column(String, unique=True, nullable=False, index=True)
    password   = Column(String, nullable=False)          # Stored as bcrypt hash
    role       = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def is_super_admin(self) -> bool:
        """Helper method: returns True only for super_admin role."""
        return self.role == UserRole.super_admin

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"