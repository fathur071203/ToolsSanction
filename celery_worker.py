"""Celery worker entrypoint.

Run (example):
    celery -A celery_worker.celery worker -l info
"""

from slis.celery_app import celery_app as celery

# Ensure task modules are imported/registered
from slis import tasks as _tasks  # noqa: F401


@celery.task
def ping():
    """
    Task uji coba.
    Nanti kita ganti/extend dengan task screening.
    """
    return "pong from Celery"
