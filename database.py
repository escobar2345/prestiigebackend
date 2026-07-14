import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from env_loader import load_env_file


load_env_file()

# ─── PostgreSQL Connection ─────────────────────────────────────
# Format: postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
# Replace these values with your actual PostgreSQL credentials
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

if DATABASE_URL == "sqlite:///./app.db":
    db_path = Path(__file__).resolve().parent / "app.db"
    DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── DB Dependency (used in route functions) ───────────────────
def get_db():
    """
    Yields a database session and ensures it's closed after use.
    Use this as a FastAPI dependency: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
