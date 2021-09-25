from integrations.dyte.service import dyte_service
from integrations.dyte import constants

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
        user(User): User object

    """
    return dyte_service.add_participant_to_meeting(dyte_meeting, user, preset_name)


def get_dyte_webinar_for_group(group):
    """Returns dyte meeting for a group.

    Args:
        group(Group): Group for which we are getting
            the dyte meeting.

    """
    return group.dyte_webinar.first()

