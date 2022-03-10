import os

from celery import Celery
from celery.schedules import crontab
from ddtrace import patch
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance.settings")

if not settings.DEBUG:
    patch(celery=True)
app = Celery('freelance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = 'UTC'
app.autodiscover_tasks()

app.conf.update(
    worker_pool_restarts=True,
)
app.conf.beat_schedule = {
    'check-transcoder-file-jobs': {
        'task': 'check_transcoding_for_cover_file',
        'schedule': crontab(minute='*/1')
    },
    'auto-remove-not-used-cover-files': {
        'task': 'auto_remove_not_used_cover_files',
        'schedule': crontab(hour=23, minute=59)
    }
}
