from __future__ import annotations

from datetime import datetime, timezone
from celery.utils.log import get_task_logger

from slis.celery_app import celery_app as celery
from slis.db import SessionLocal
from slis.services.screening import run_screening_for_job

logger = get_task_logger(__name__)

@celery.task(bind=True, name="slis.run_screening_task")
def run_screening_task(self, job_id: int) -> dict:
    """Celery entrypoint that runs the same DB-backed engine used by web fallback.

    This keeps behavior consistent: thresholds are enforced during matching,
    sanction_source_filter is respected, and progress is stored in DB.
    """
    db = SessionLocal()
    try:
        # Note: run_screening_for_job handles status/progress and error capture.
        run_screening_for_job(db=db, job_id=job_id)
        return {"job_id": job_id, "status": "DONE"}
    finally:
        db.close()