import logging

from celery.task import task
from django.contrib.auth import get_user_model

from conversations import models
from conversations import signals

User = get_user_model()

LOGGER = logging.getLogger(__name__)


@task()
def add_attendee_to_group_for_request(attendee_pk, group_request_id):
    """Add user to group as an attendee.

    Args:
        attendee_pk(uuid): PK of attendee to be added to group
        group_request_id(int): Request ID of the group to which user to be added

    """
    try:
        attendee = User.objects.get(pk=attendee_pk)
        group_request = models.Request.objects.get(
            id=group_request_id
        )
    except (User.DoesNotExist, models.Request.DoesNotExist) as e:
        LOGGER.error(str(e))
        return False

    group_request.group.attendees.add(attendee)

    # Send a signal once user is added to the group.
    signals.attendee_added_to_group.send(
        sender=group_request.group.__class__,
        group=group_request.group,
        user=attendee
    )


@task()
def add_attendee_to_series(attendee_pk, series_id, series_request_ids):
    """Add user to series as an attendee.

    Args:
        attendee_pk(uuid): PK of attendee to be added to series.
        series_id(int): ID of series to which attendee needs to be added.
        series_request_ids(list(int)): Series request ids for user.

    """

    try:
        attendee = User.objects.get(pk=attendee_pk)
        series = models.Series.objects.get(
            id=series_id
        )
        series_requests = models.Request.objects.filter(
            id__in=series_request_ids
        )
    except (User.DoesNotExist, models.Series.DoesNotExist) as e:
        LOGGER.error(str(e))
        return False

    # Update request status and add attendee to request group
    for request in series_requests:
        request.group.attendees.add(attendee)

    # Send a signal once user is added to the series.
    signals.attendee_added_to_series.send(
        sender=series.__class__,
        series=series,
        series_requests=series_requests,
        user=attendee
    )
