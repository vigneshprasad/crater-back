import os

from celery import Celery
from celery.schedules import crontab
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
    worker_pool_restarts=True
)

app.conf.beat_schedule = {
    "send_stream_going_live_notifications_weekend_12_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=6, minute=30, day_of_week="0,6")
    },
    "send_stream_going_live_notifications_weekend_2_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=8, minute=30, day_of_week="0,6")
    },
    "send_stream_going_live_notifications_weekend_4_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=10, minute=30, day_of_week="0,6")
    },
    "send_stream_going_live_notifications_weekday_4_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=10, minute=30, day_of_week="1-5")
    },
    "send_stream_going_live_notifications_weekday_6_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=12, minute=30, day_of_week="1-5")
    },
    "send_stream_going_live_notifications_weekday_8_pm": {
        "task": "communications.notifications.tasks.send_groups_going_live_notifications",
        "schedule": crontab(hour=14, minute=30, day_of_week="1-5")
    },
}
