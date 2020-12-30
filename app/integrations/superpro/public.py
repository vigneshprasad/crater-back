from integrations.superpro.service import superpro_test_service


def create_meeting_link(meeting):
    """Create video call URI for a meeting.

    Args:
        meeting(Meeting): Meeting object.

    """
    users = meeting.participants.all()
    meeting_link = superpro_test_service.create_video_call(users)
    return meeting_link
