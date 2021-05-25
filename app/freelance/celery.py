import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance.settings')

app = Celery('freelance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = 'UTC'
app.conf.broker_url = 'redis://localhost:6379/0'
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
    },
    'check-subscription': {
        'task': 'check_subscription',
        'schedule': crontab(hour=0, minute=1)
    },
    'send-warning': {
        'task': 'send_subs_warning_email',
        'schedule': crontab(hour=0, minute=1)
    },
    'auto-refresh-instagram-long-access-token': {
        'task': 'auto_refresh_instagram_long_access_token',
        'schedule': crontab(hour=0, minute=5)
    }
    # 'send_email_for_unread_messages': {
    #     'task': 'send_email_for_unread_messages',
    #     'schedule': crontab(minute='*/15')
    # }
}
