# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load dari .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database connection string
    # - If SLIS_USE_LOCAL_DB=1, force local SQLite.
    # - Else if DATABASE_URL is set, use it (e.g. Neon Postgres).
    # - Else default to local SQLite file.
    _REPO_ROOT = Path(__file__).resolve().parent
    _DEFAULT_SQLITE_PATH = (_REPO_ROOT / "data" / "local_db" / "slis.db").resolve()
    _USE_LOCAL_DB = (os.getenv("SLIS_USE_LOCAL_DB") or "").strip().lower() in {"1", "true", "yes", "y", "on"}
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{_DEFAULT_SQLITE_PATH}"
        if _USE_LOCAL_DB
        else (os.getenv("DATABASE_URL") or f"sqlite:///{_DEFAULT_SQLITE_PATH}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery + Redis
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False
