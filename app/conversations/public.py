import logging

from django.conf import settings
from django.core.exceptions import ValidationError

from conversations import constants, models


def get_livestream_link_for_webinar(group):
    """Returns the livestream link for a group.

    Args:
        group(Group): Group we are getting the link for.

    """
    front_url = settings.CRATER_FRONT_URL
    livestream_url = front_url + constants.LIVESTREAM_URL_WITH_GROUP.format(
        group_id=group.id
    )
    return livestream_url


def get_session_link_for_webinar(group):
    """Returns the session link for a group.

    Args:
        group(Group): Group we are getting the link for.

    """
    front_url = settings.CRATER_FRONT_URL
    session_url = front_url + constants.SESSION_URL_WITH_GROUP.format(
        group_id=group.id
    )
    return session_url


def get_video_page_for_webinar(group):
    """Returns the video page link for a group.

    Args:
        group(Group): Group we are getting the link for.

    Note:
        Only past streams will have a video page link.

    """
    front_url = settings.CRATER_FRONT_URL
    video_url = front_url + constants.VIDEO_URL_WITH_GROUP.format(
        group_id=group.id
    )
    return video_url


def create_group_message(
        sender,
        group,
        display_name,
        message,
        message_type=constants.CHAT_MESSAGE_TYPE_TEXT_ENUM,
        message_data=None,
        firebase_message_id=None,
        created_at=None
):
    """Create group message in the DB.

    Args:
        sender(User): User (object) who sent the message.
        group(Group): Stream on which the message was sent.
        display_name(str): Display name used by the sender.
        message(text): Message sent by the user.
        message_type(int): Type of message that was sent.
        message_data(dict): Extra message data like image url etc.
        firebase_message_id(str): ID of the message in firestore.
        created_at(datetime.datetime): Timestamp of creation on firebase's end.

    """
    try:
        group_message = models.GroupMessage.objects.create(
            group=group,
            sender=sender,
            message=message,
            display_name=display_name,
            type=message_type,
            data=message_data,
            firebase_message_id=firebase_message_id
        )
    except ValidationError as e:
        logging.error(str(e))
        return

    # Update the created at to the firestore created_at timestamp.
    if created_at:
        group_message.created_at = created_at
        group_message.save()

    return group_message
