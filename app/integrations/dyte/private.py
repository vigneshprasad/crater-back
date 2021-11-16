from django.core.exceptions import ValidationError

from integrations.dyte import constants
from integrations.dyte import models


def get_dyte_participant_for_user_and_group(user, group):
    """Return dyte meeting participant for a user and group.

    Args:
        user(User): User who is the dyte participant.
        group(Group): Group of which the user should be
            part of.

    """
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        return False

    return user.dyte_participant.filter(
        dyte_meeting=dyte_meeting
    ).first()


def get_dyte_meeting_for_dyte_meeting_id(dyte_meeting_id):
    """Returns dyte meeting for give dyte meeting id.

    Args:
        dyte_meeting_id(str): Dyte meeting on the dyte servers.

    """
    if not dyte_meeting_id:
        return None

    return models.DyteMeeting.objects.filter(
        dyte_meeting_id=dyte_meeting_id
    ).first()


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
