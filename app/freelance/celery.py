import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance.settings')

app = Celery('freelance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = 'UTC'
app.conf.broker_url = 'redis://localhost:6379/0'
app.autodiscover_tasks()

app.conf.update(
    worker_pool_restarts=True,
)
