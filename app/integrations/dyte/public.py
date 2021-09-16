from integrations.dyte.service import dyte_service


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


def add_participant_to_meeting(dyte_meeting, user):
    """Add a participant to dyte_meeting

    Args:
        dyte_meeting(DyteMeeting): DyteMeeting object.
        user(User): User object

    """
    return dyte_service.add_participant_to_meeting(dyte_meeting, user)
