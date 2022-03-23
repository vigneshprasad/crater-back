import os

from celery import Celery
from ddtrace import patch
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance.settings")

if not settings.DEBUG:
    patch(celery=True)

app = Celery("freelance")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.timezone = "UTC"
app.autodiscover_tasks()

app.conf.update(
    worker_pool_restarts=True,
)
