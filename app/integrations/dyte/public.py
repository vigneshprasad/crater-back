from integrations.dyte.service import dyte_service


def create_meeting(meeting):
    """Create meeting on Dyte for Meeting object.

    Args:
        meeting(Meeting): Meeting object.

    """
    return dyte_service.create_meeting(meeting)
