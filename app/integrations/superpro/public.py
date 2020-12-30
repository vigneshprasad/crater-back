from integrations.superpro.service import superpro_service
from integrations.superpro import models


def create_meeting_link(meeting):
    """Create video call URI for a meeting.

    Args:
        meeting(Meeting): Meeting object.

    """
    users = meeting.participants.all()
    video_call_id, video_call_uri = superpro_service.create_video_call(users)

    # Creating model entry for the Meeting room created.
    for user in users:
        # In case we got a bad response from SuperPro.
        if not video_call_id and video_call_uri:
            continue
        models.VideoCall.objects.create(
            user=user,
            video_call_id=video_call_id,
            video_call_uri=video_call_uri
        )

    return video_call_uri
