from celery.task import task
from django.contrib.auth import get_user_model

from conversations import models as conversation_models
from integrations.google import private


@task()
def create_calendar_events_for_series_attendee(series_id, user_id):
    """Creates calendar events for serie's groups for attendee"""

    try:
        user = get_user_model().objects.get(uuid=user_id)
        series = conversation_models.Series.objects.get(id=series_id)
    except (get_user_model().DoesNotExist, conversation_models.Series.DoesNotExist):
        return False

    groups = series.groups.filter(
        is_live=False,
        closed=False
    )
    if not groups:
        return False

    for group in groups:
        private.create_calendar_event_for_webinar_attendee(user, group)
