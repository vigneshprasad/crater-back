import datetime
import logging

from celery.schedules import crontab
from celery.task import periodic_task, task
from django.utils import timezone

from conversations import models as conversations_models
from integrations.dyte import constants, models, service
from tokens import tasks as token_tasks

dyte_service = service.dyte_service

LOGGER = logging.getLogger(__name__)


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
    participants_went_online_for_all_groups = models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group__in=live_groups,
        last_online_at__isnull=False
    )

    for group in live_groups:
        participants_went_online_for_group = participants_went_online_for_all_groups.filter(
            dyte_meeting__group=group
        )
        dyte_participant_for_host = participants_went_online_for_group.filter(
            participant_id=group.host_id
        ).last()
        if not dyte_participant_for_host:
            continue

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # Update host minutes_spent.
        dyte_participant_for_host.minutes_spent = host_total_minutes
        dyte_participant_for_host.save()
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        dyte_participants_for_attendees = participants_went_online_for_group.exclude(id=dyte_participant_for_host.id)
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

    # Send another task to update tokens.
    token_tasks.calculate_tokens_for_groups.delay(
        list(live_groups.values_list("id", flat=True))
    )


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

    participants_went_online_for_all_groups = models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group__in=groups_in_the_last_day,
        last_online_at__isnull=False
    )

    for group in groups_in_the_last_day:
        participants_went_online_for_group = participants_went_online_for_all_groups.filter(
            dyte_meeting__group=group
        )

        dyte_participant_for_host = participants_went_online_for_group.filter(
            participant_id=group.host_id
        ).last()
        if not dyte_participant_for_host:
            continue

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # Update host minutes_spent.
        dyte_participant_for_host.minutes_spent = host_total_minutes
        dyte_participant_for_host.save()
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        dyte_participants_for_attendees = participants_went_online_for_group.exclude(id=dyte_participant_for_host.id)
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

    # Send another task to update tokens.
    token_tasks.calculate_tokens_for_groups.delay(
        list(groups_in_the_last_day.values_list("id", flat=True))
    )


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

    participants_went_online_for_all_groups = models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group__in=groups,
        last_online_at__isnull=False
    )

    for group in groups:
        participants_went_online_for_group = participants_went_online_for_all_groups.filter(
            dyte_meeting__group=group
        )

        dyte_participant_for_host = participants_went_online_for_group.filter(
            participant_id=group.host_id
        ).last()
        if not dyte_participant_for_host:
            continue

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # Update host minutes_spent.
        dyte_participant_for_host.minutes_spent = host_total_minutes
        dyte_participant_for_host.save()

        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        dyte_participants_for_attendees = participants_went_online_for_group.exclude(id=dyte_participant_for_host.id)
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

    # Send another task to update tokens.
    token_tasks.calculate_tokens_for_groups.delay(
        list(groups.values_list("id", flat=True))
    )


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
            file_size = recording_data.get("fileSize") or 0
            file_size_mb = round(file_size / (1024 * 1024), 2)
        except KeyError:
            return False

        # Update the status.
        dyte_meeting_active_recording.status = status
        dyte_meeting_active_recording.file_size = file_size_mb
        dyte_meeting_active_recording.save()

        # Update start and stop times.
        dyte_meeting_active_recording.update_start_and_stop_times(started_at, stopped_at)


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
            file_size = recording_data.get("fileSize") or 0
            file_size_mb = round(file_size / (1024 * 1024), 2)
        except KeyError:
            return False

        # Update the status.
        dyte_meeting_recording.status = status
        dyte_meeting_recording.file_size = file_size_mb
        dyte_meeting_recording.save()
        # Update start and stop times.
        dyte_meeting_recording.update_start_and_stop_times(started_at, stopped_at)


@task()
def mark_dyte_meeting_participants_offline(group_id):
    """Mark dyte participants for a stream once it's closed.

    Note:
        Only dyte participants who are not marked offline
            through webhook are marked offline with this.

    """
    group = conversations_models.Group.objects.get(id=group_id)
    online_dyte_participants = models.DyteMeetingParticipant.objects.filter(
        is_online=True,
        dyte_meeting__group=group
    )

    for dyte_participant in online_dyte_participants:
        group = dyte_participant.dyte_meeting.group
        online_logs = dyte_participant.online_logs.all()
        online_online_logs = online_logs.filter(is_offline=False)
        last_online_log = online_logs.last()
        offline_time = last_online_log.offline_at if last_online_log else group.last_live_at

        # Mark all online logs offline.
        for log in online_online_logs:
            log.offline_at = offline_time
            log.is_offline = True
            log.save()

        # Mark dyte participant offline
        dyte_participant.last_online_at = offline_time
        dyte_participant.is_online = False
        dyte_participant.save()


@task()
def start_recording_for_group(group_id):
    """Start recording for a group.

    Args:
        group_id(int): ID of the group we are
            starting the recording for.

    """
    group = conversations_models.Group.objects.get(id=group_id)
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        logging.error("Dyte meeting not present for group: {}".format(group.id))
        return False

    return dyte_service.start_recording(dyte_meeting=dyte_meeting)
