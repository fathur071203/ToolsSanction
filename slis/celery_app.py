from celery import Celery
from config import Config

# INI INSTANCE CELERY YANG DIPAKAI SEMUA
celery_app = Celery(
    "slis",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=["slis.tasks.db_job"]
)

# (opsional) set queue default
celery_app.conf.task_default_queue = "default"
