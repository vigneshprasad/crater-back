import logging

from celery import shared_task
from celery.task import task
from django.contrib.auth import get_user_model
from django.utils import timezone

from integrations.google import constants
from integrations.google import models
from integrations.google import private
from conversations import models as conversation_models


@task
def create_calendar_events_for_series_attendee(series_id, user_id):
    """Creates calendar events for series' groups for attendee"""

    try:
        user = get_user_model().objects.get(uuid=user_id)
        series = conversation_models.Series.objects.get(id=series_id)
        groups = series.groups.filter(
            is_live=False,
            closed=False
        )
        if not groups:
            return

        for group in groups:
            private.create_calendar_event_for_webinar_attendee(user, group)

    except (get_user_model().DoesNotExist, conversation_models.Series.DoesNotExist):
        return

