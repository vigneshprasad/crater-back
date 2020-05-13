from datetime import datetime

from resources.events.models import Event, RSVPD
from resources.events.serializers import EventSerializer


def get_datetime_now():
    return datetime.now()


def set_going_event():
    for event in Event.objects.filter(state='upcoming'):
        now = get_datetime_now()
        start = datetime.combine(event.date, event.start)
        end = datetime.combine(event.date, event.end)
        if start < now < end:
            event.state = 'going'
            event.save(update_fields=['state'])


def set_past_events():
    for event in Event.objects.exclude(state='past'):
        now = get_datetime_now()
        if datetime.combine(event.date, event.end) < now:
            event.state = 'past'
            event.save(update_fields=['state'])


def get_events():
    return Event.objects.all()


def get_event_pk_by_participant(event_pk, user_pk):
    try:
        participant = Event.objects.get(pk=event_pk).participants.get(user=user_pk)
        if participant:
            return participant.pk
    except (Event.DoesNotExist, RSVPD.DoesNotExist):
        return event_pk


def get_event(pk):
    return Event.objects.get(pk=pk)


def get_first_event_data():
    event = Event.objects.first()
    if event:
        return EventSerializer(event).data
