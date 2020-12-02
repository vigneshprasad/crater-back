import logging

from celery import shared_task
from django.utils import timezone

from integrations.google import constants
from integrations.google import models
from integrations.google import private


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

