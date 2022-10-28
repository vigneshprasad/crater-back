from celery.task import task
from django.core.exceptions import ValidationError

from integrations.dyte import constants, models, service


def get_dyte_participant_for_user_and_group(user, group):
    """Return dyte meeting participant for a user and group.

    Args:
        user(User): User who is the dyte participant.
        group(Group): Group of which the user should be
            part of.

    """
    dyte_meeting = group.dyte_meeting
    if not dyte_meeting:
        return False

    return user.dyte_participant.filter(
        dyte_meeting=dyte_meeting
    ).first()


def get_preset_for_group(user, group):
    """Returns correct preset based on whether we need
        preset for host or participant and the group.

    Args:
        user(User): User for whom we are getting the preset.
        group(Group): Group for which we are getting the preset for

    """
    participant = False if user in group.get_host_and_speakers() else True

    if participant and group.is_obs:
        # If the user is a participant and group is obs.
        # Return OBS preset for participant
        return constants.WEBINAR_OBS_PARTICIPANT_PRESET_NAME
    elif participant and not group.is_obs:
        # If the user is a participant and group is not obs.
        # Return default preset for participant.
        return constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME
    elif not participant and group.is_obs:
        # If the user is not a participant and group is obs.
        # Return OBS preset for host.
        return constants.WEBINAR_OBS_HOST_PRESET_NAME
    elif not (participant and group.is_obs):
        # If the user is not a participant and group is not obs.
        # Return default preset for host.
        return constants.DEFAULT_WEBINAR_HOST_PRESET_NAME
    else:
        return constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME


def get_group_for_dyte_meeting_id(dyte_meeting_id):
    """Returns stream for give dyte meeting id.

    Args:
        dyte_meeting_id(str): Dyte meeting on the dyte servers.

    """
    if not dyte_meeting_id:
        return None

    dyte_meeting = models.DyteMeeting.objects.filter(
        dyte_meeting_id=dyte_meeting_id
    ).first()

    return dyte_meeting.group if dyte_meeting else dyte_meeting


def get_participant_for_user_id_and_dyte_meeting_id(user_pk, dyte_meeting_id):
    """Get Dyte participant for a user and group id.

    Args:
        user_pk(uuid): User pk for which are getting the dyte participant.
        dyte_meeting_id(uuid): Dyte Meeting ID of which the participant is
            a part of.

    """
    if not (user_pk and dyte_meeting_id):
        return None

    try:
        participant = models.DyteMeetingParticipant.objects.get(
            participant_id=user_pk,
            dyte_meeting__dyte_meeting_id=dyte_meeting_id
        )
    except (models.DyteMeetingParticipant.DoesNotExist, ValidationError):
        return None

    return participant


def get_participant_for_user_and_group_id(user, group_id):
    """Get Dyte participant for a user and group id.

    Args:
        user(User): User for which are getting the dyte participant.
        group_id(int): Group ID of which the participant is
            a part of.

    """
    try:
        participant = models.DyteMeetingParticipant.objects.get(
            participant=user,
            dyte_meeting__group_id=group_id
        )
    except models.DyteMeetingParticipant.DoesNotExist:
        return None

    return participant


def get_dyte_meeting_recording_for_recording_id(recording_id):
    """Get Dyte meeting recording for a recording id.

    Args:
        recording_id(str): Dyte meeting recording id.

    """
    try:
        dyte_meeting_recording = models.DyteMeetingRecording.objects.get(
            recording_id=recording_id
        )
    except models.DyteMeetingRecording.DoesNotExist:
        return None

    return dyte_meeting_recording


def get_active_recording_for_dyte_meeting(dyte_meeting):
    """Returns active recording going on for a live stream.

    Args:
        dyte_meeting(DyteMeeting): Dyte meeting object.

    """
    dyte_meeting_active_recording = models.DyteMeetingRecording.objects.filter(
        dyte_meeting=dyte_meeting,
        status__in=[
            constants.DYTE_RECORDING_STATUS_INVOKED,
            constants.DYTE_RECORDING_STATUS_RECORDING
        ]
    ).first()

    return dyte_meeting_active_recording


def get_recording_for_dyte_meeting_and_status(
        dyte_meeting,
        status=constants.DYTE_RECORDING_STATUS_RECORDING
):
    """Return recording id for recording to stop for a Dyte meeting.

    Args:
        dyte_meeting(DyteMeeting): DyteMeeting object
        status(str): Status of recording we are getting.

    Returns:
        recording_id(str): Recording ID on dyte's end we
            need to stop.

    """

    # Only recordings in RECORDING status can be stopped.
    recording_to_stop = dyte_meeting.meeting_recording.filter(
        status=status
    ).last()

    if not recording_to_stop:
        return None

    return recording_to_stop.recording_id


@task
def mark_participants_offline_for_group(group):
    """Marks all dyte participants offline on our end once
        the meeting ends.

    Args:
        group(Group): Group that was marked closed from Dyte's end.

    """
    dyte_meeting = group.dyte_webinar.last()
    if not dyte_meeting:
        return False

    # Get all participants for the dyte meeting.
    participants = dyte_meeting.meeting_participants.filter(is_online=True)
    for participant in participants:
        # If the dyte participant is not offline, mark it offline.
        participant.mark_offline()

        # Mark all logs offline as well.
        participant_online_logs = participant.online_logs.filter(is_offline=False)
        for online_log in participant_online_logs:
            online_log.mark_offline()


def get_livestream_object_for_stream_id(stream_id):
    """Return livestream object for a stream id.

    Args:
        stream_id(str): Live stream ID on dyte's end.

    """
    try:
        livestream = models.LiveStream.objects.get(livestream_id=stream_id)
    except models.LiveStream.DoesNotExist:
        livestream = service.dyte_service_v2.get_details_of_livestream(stream_id)

    return livestream
