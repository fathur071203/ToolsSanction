from __future__ import annotations

from sqlalchemy import inspect, text

from slis.db import engine


def ensure_schema() -> None:
    """Ensure DB has required columns for new features.

    Repo intentionally doesn't use Alembic migrations; this provides a minimal,
    safe auto-upgrade path for small additive changes.
    """

    insp = inspect(engine)
    try:
        cols = {c["name"] for c in insp.get_columns("screening_job")}
    except Exception:
        return

    if "sanction_source_filter" not in cols:
        stmt = text("ALTER TABLE screening_job ADD COLUMN sanction_source_filter TEXT")
        with engine.begin() as conn:
            conn.execute(stmt)
