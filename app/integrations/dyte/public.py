import logging

from integrations.dyte import constants, private, models
from integrations.dyte.service import dyte_service, dyte_service_v2


def create_meeting_link(meeting):
    """Create meeting on Dyte for Meeting object.

    Args:
        meeting(Meeting): Meeting object.

    """
    return dyte_service.create_meeting(meeting)


def create_webinar(group):
    """Create a webinar on Dyte for Group object

    Args:
        group(Group): Group object.

    """
    return dyte_service.create_webinar(group)


def add_participant_to_meeting(
        dyte_meeting,
        user,
        preset_name=constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME
):
    """Add a participant to dyte_meeting

    Args:
        dyte_meeting(DyteMeeting): DyteMeeting object.
        user(User): User object.
        preset_name(str): Preset name for the dyte participant
            we are adding.

    """
    return dyte_service.add_participant_to_meeting(dyte_meeting, user, preset_name)


def get_dyte_webinar_for_group(group):
    """Returns dyte meeting for a group.

    Args:
        group(Group): Group for which we are getting
            the dyte meeting.

    """
    return group.dyte_webinar.first()


def get_dyte_participant_for_user_and_group(user, group):
    """Return dyte participant for a user and group.

    Args:
        user(User): User for which are getting the dyte participant.
        group(Group): Group object for which the participant is
            present.

    """
    return private.get_participant_for_user_and_group_id(
        user=user,
        group_id=group.id
    )


def start_recording_for_group(group):
    """Start Dyte meeting recording

    Args:
        group(Group): Group we are starting the recording
            for.

    """
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        logging.error("Dyte meeting not present for group: {}".format(group.id))
        return False

    return dyte_service.start_recording(dyte_meeting=dyte_meeting)
    # TODO(Nishant): Start recording on online is going to celery now and
    # sometimes it affects normal task for starting 5 minutes before.
    # Might have to move that also to the same task.
    # return tasks.start_recording_for_meeting_if_required.apply_async(
    #     args=(group.id, ),
    #     coutdown=5
    # )


def get_recordings_for_group(group):
    """Get Dyte meeting recording

    Args:
        group(Group): Group we are getting the recordings
            for.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return None

    return dyte_service.get_all_recordings(dyte_meeting=dyte_meeting)


def stop_recording_for_group_and_recording_id(group, recording_id=None):
    """Stop recording for a group.

    Args:
        group(Group): Group we are stopping the recording
            for.
        recording_id(str): Dyte meeting recording id for
            recording.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        logging.error("Dyte meeting not present for group: {}".format(group.id))
        return False

    recording_id = private.get_recording_for_dyte_meeting_and_status(
        dyte_meeting,
        status=constants.DYTE_RECORDING_STATUS_RECORDING
    ) if not recording_id else recording_id

    if not recording_id:
        return False

    return dyte_service.stop_recording(dyte_meeting, recording_id)


def get_active_livestream_for_stream_id(group_id):
    """Get active Dyte LiveStream for a Webinar

    Args:
        group_id(int): ID of stream for which are getting the
            livestream.

    """
    try:
        dyte_meeting = models.DyteMeeting.objects.get(group_id=group_id)
    except models.DyteMeeting.DoesNotExist:
        return False

    dyte_service_v2.get_active_livestream(dyte_meeting)
