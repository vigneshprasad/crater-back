from freelance.celery import app
from celery.decorators import periodic_task
from datetime import timedelta
from django.core.mail import send_mail

from resources.events.services import set_past_events, set_going_event


@periodic_task(run_every=timedelta(minutes=10))
def expire_events():
    set_going_event()
    set_past_events()


@app.task
def send_email(title, message, _from, to):
    send_mail(title, message, _from, [to])
