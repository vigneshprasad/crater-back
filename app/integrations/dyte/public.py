from integrations.dyte.service import dyte_service
from integrations.dyte import constants
from integrations.dyte import private


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
        return None

    return dyte_service.start_recording(
        room_name=dyte_meeting.room_name
    )


def get_recordings_for_group(group):
    """Get Dyte meeting recording

    Args:
        group(Group): Group we are getting the recordings
            for.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return None

    return dyte_service.get_all_recordings(
        dyte_meeting_id=dyte_meeting.dyte_meeting_id
    )


def stop_recording_for_group_and_recording_id(group, recording_id):
    """Stop Dyte meeting recording

    Args:
        group(Group): Group we are stopping the recording
            for.
        recording_id(str): Dyte meeting recording id for
            recording.

    """
    dyte_meeting = group.dyte_webinar.first()
    if not dyte_meeting:
        return None

    return dyte_service.stop_recording(dyte_meeting.room_name, recording_id)
