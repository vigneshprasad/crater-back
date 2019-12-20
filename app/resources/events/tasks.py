from celery.decorators import periodic_task
from datetime import timedelta

from resources.events.services import set_past_events, set_going_event


@periodic_task(run_every=timedelta(minutes=10))
def expire_events():
    set_going_event()
    set_past_events()
