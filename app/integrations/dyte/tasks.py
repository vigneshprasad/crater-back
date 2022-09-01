import datetime

from celery.schedules import crontab
from celery.task import periodic_task, task
from django.utils import timezone

from conversations import models as conversations_models
from integrations.dyte import models, service, constants

dyte_service = service.dyte_service


@periodic_task(run_every=crontab("*/5"))
def get_minutes_for_live_streams():
    """Get minutes of live streams from Dyte's end and update on
        our models.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    now = timezone.now()
    live_groups = conversations_models.Group.objects.filter(
        is_live=True,
        is_published=True,
        closed=False,
        start__lte=now
    )

    for group in live_groups:
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()


@periodic_task(run_every=crontab(hour="0", minute="0"))
def get_minutes_for_all_streams_for_the_day():
    """Get minutes of yesterday's streams from Dyte's end and update on
        our models.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    today = timezone.now()
    yesterday = today - datetime.timedelta(days=1)
    groups_in_the_last_day = conversations_models.Group.objects.filter(
        is_published=True,
        closed=True,
        start__lte=today,
        start__gte=yesterday
    )

    for group in groups_in_the_last_day:
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()


@task()
def recalculate_minutes_for_groups(group_ids):
    """Get minutes of live streams from Dyte's end and update on
        our models.

    Args:
        group_ids(list/queryset): Group ids we want to recalculate
            minutes for.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    groups = conversations_models.Group.objects.filter(
        id__in=group_ids
    )

    for group in groups:
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()


@task()
def start_recording_for_meeting_if_required(group_id):
    """Starts meeting recording for a group if required.

    Args:
        group_id(int): ID of the group we want to record.

    Note:
        Will only start recording if there are no active
            recordings at the moment.

    """
    group = conversations_models.Group.objects.get(id=group_id)
    dyte_meeting = group.dyte_webinar.first()
    # Update the meeting recording status from Dyte's end.
    update_meeting_recording_status_for_active_recordings(group_id)

    # Get active recordings if any.
    dyte_meeting_active_recordings = models.DyteMeetingRecording.objects.filter(
        dyte_meeting=dyte_meeting,
        status__in=[
            constants.DYTE_RECORDING_STATUS_INVOKED,
            constants.DYTE_RECORDING_STATUS_RECORDING
        ]
    )

    if dyte_meeting_active_recordings:
        return False

    dyte_service.start_recording(dyte_meeting)


@task()
def update_meeting_recording_status_for_active_recordings(group_id):
    """Update meeting recording status for all recordings of a
        stream/group, if we haven't got and update from Dyte's end.

    Args:
        group_id(int): ID of the group we are updating recording
            status for.
    """
    group = conversations_models.Group.objects.get(id=group_id)
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return False

    # Get all recording in recording or invoked state.
    dyte_meeting_active_recordings = models.DyteMeetingRecording.objects.filter(
        dyte_meeting=dyte_meeting,
        status__in=[
            constants.DYTE_RECORDING_STATUS_INVOKED,
            constants.DYTE_RECORDING_STATUS_RECORDING
        ]
    )

    if not dyte_meeting_active_recordings:
        return True

    for dyte_meeting_active_recording in dyte_meeting_active_recordings:
        recording_data = service.dyte_service.get_recording(
            dyte_meeting.dyte_meeting_id,
            dyte_meeting_active_recording.recording_id
        )
        if not recording_data:
            continue

        try:
            status = recording_data["status"]
            started_at = recording_data["startedTime"]
            stopped_at = recording_data["stoppedTime"]
        except KeyError:
            return False

        # Update the status.
        dyte_meeting_active_recording.status = status

        try:
            dyte_meeting_active_recording.started_at = datetime.datetime.strptime(
                started_at, constants.DYTE_DATETIME_FORMAT
            ) if started_at else None
            dyte_meeting_active_recording.stopped_at = datetime.datetime.strptime(
                stopped_at, constants.DYTE_DATETIME_FORMAT
            ) if stopped_at else None
        except ValueError:
            dyte_meeting_active_recording.started_at = None
            dyte_meeting_active_recordings.stopped_at = None

        dyte_meeting_active_recording.save()

    return True


@task()
def update_meeting_recording_status_for_recording_ids(recording_ids):
    """Update meeting recording status for all provided recording ids.

    Args:
        recording_ids(list/queryset): ID's of the recording we are updating.

    """
    dyte_meeting_recordings = models.DyteMeetingRecording.objects.filter(
        id__in=recording_ids
    )
    if not dyte_meeting_recordings:
        return

    for dyte_meeting_recording in dyte_meeting_recordings:
        dyte_meeting = dyte_meeting_recording.dyte_meeting
        recording_data = service.dyte_service.get_recording(
            dyte_meeting.dyte_meeting_id,
            dyte_meeting_recording.recording_id
        )
        if not recording_data:
            continue

        try:
            status = recording_data["status"]
            started_at = recording_data["startedTime"]
            stopped_at = recording_data["stoppedTime"]
        except KeyError:
            return False

        # Update the status.
        dyte_meeting_recording.status = status

        try:
            dyte_meeting_recording.started_at = datetime.datetime.strptime(
                started_at, constants.DYTE_DATETIME_FORMAT
            ) if started_at else None
            dyte_meeting_recording.stopped_at = datetime.datetime.strptime(
                stopped_at, constants.DYTE_DATETIME_FORMAT
            ) if stopped_at else None
        except ValueError:
            dyte_meeting_recording.started_at = None
            dyte_meeting_recording.stopped_at = None

        dyte_meeting_recording.save()
