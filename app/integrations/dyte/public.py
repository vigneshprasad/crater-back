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


def get_livestream_for_stream_and_status(
        group,
        status=constants.LIVE_STREAM_STATUS_LIVE
):
    """Get active Dyte LiveStream for a Webinar

    Args:
        group(Group): Stream for which are starting the
            livestream.
        status(str): Status of livestream we want to get.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return False

    return models.LiveStream.objects.filter(
        dyte_meeting=dyte_meeting,
        status=status
    ).last()


def start_livestream_for_stream(group):
    """Start Dyte liveStream for a stream.

    Args:
        group(Group): Stream for which are starting the
            livestream.

    """

    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return False

    active_livestream = get_livestream_for_stream_and_status(
        group,
        status=constants.LIVE_STREAM_STATUS_LIVE
    )
    # If there is an active livestream, don't start again.
    if active_livestream:
        return False

    return dyte_service_v2.start_livestream_for_meeting(dyte_meeting)


def stop_livestream_for_stream(group):
    """Stop active Dyte livestream for a stream.

    Args:
        group(Group): Stream for which are starting the
            livestream.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return False

    active_livestream = get_livestream_for_stream_and_status(
        group,
        status=constants.LIVE_STREAM_STATUS_LIVE
    )
    # If there is no active livestream, don't stop.
    if not active_livestream:
        return False

    return dyte_service_v2.stop_active_livestream_meeting(dyte_meeting)
