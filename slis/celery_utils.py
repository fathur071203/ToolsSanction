from __future__ import annotations

import os
import socket
from typing import Optional
from urllib.parse import urlparse

from slis.celery_app import celery_app


def _redis_reachable(broker_url: str, timeout_s: float = 0.25) -> bool:
    try:
        u = urlparse(broker_url)
    except Exception:
        return False

    if u.scheme not in {"redis", "rediss"}:
        # Unknown broker; don't attempt to probe.
        return True

    host = u.hostname or "localhost"
    port = int(u.port or 6379)

    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except Exception:
        return False


def celery_enabled() -> bool:
    return os.getenv("SLIS_DISABLE_CELERY", "0") != "1"


def enqueue_screening_job(job_id: int) -> Optional[str]:
    """Try enqueue to Celery, return task id if queued; else None.

    This avoids raising noisy OperationalError when Redis isn't running.
    """
    if not celery_enabled():
        return None

    broker_url = str(getattr(celery_app.conf, "broker_url", None) or getattr(celery_app.conf, "broker", "") or "")
    if broker_url and not _redis_reachable(broker_url):
        return None

    try:
        async_result = celery_app.send_task("slis.run_screening_task", args=[job_id])
        return async_result.id
    except Exception:
        return None
