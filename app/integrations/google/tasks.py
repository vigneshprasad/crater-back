import logging

from celery import shared_task
from celery.task import task
from django.contrib.auth import get_user_model
from django.utils import timezone

from integrations.google import constants
from integrations.google import models
from integrations.google import private
from conversations import models as conversation_models


@shared_task()
def update_calendar_statuses_for_users(users=None, meetings=None):
    """Updates the calendar status for non-RSVPed users."""
    pending_google_calendar_events = models.GoogleCalendarEvent.objects.filter(
        ends_at__gte=timezone.now(),
        status__in=constants.PENDING_CALENDAR_STATUSES
    )

    for pending_google_calendar_event in pending_google_calendar_events:
        user = pending_google_calendar_event.user
        logging.info("Updating response status for {}".format(user.email))
        private.get_and_update_response_status_for_user(user)


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

