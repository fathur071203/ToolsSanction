from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from pathlib import Path

# DATABASE_URL dari .env
from dotenv import load_dotenv
load_dotenv()

def _env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


DATABASE_URL = os.getenv("DATABASE_URL")
USE_LOCAL_DB = _env_truthy(os.getenv("SLIS_USE_LOCAL_DB"))

if USE_LOCAL_DB or not DATABASE_URL:
    repo_root = Path(__file__).resolve().parents[1]
    local_db_dir = (repo_root / "data" / "local_db")
    local_db_dir.mkdir(parents=True, exist_ok=True)
    local_db_path = (local_db_dir / "slis.db").resolve()
    DATABASE_URL = f"sqlite:///{local_db_path}"

engine_kwargs = {
    "echo": False,
    "future": True,
}

if DATABASE_URL.startswith("sqlite:"):
    # Allow usage from different threads in dev server
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Neon/Postgres recommended: NullPool (avoid connection drop)
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base model untuk seluruh ORM
Base = declarative_base()

def get_db():
    """Dependency injection style (untuk Flask route)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
