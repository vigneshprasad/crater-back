import logging

from integrations.wati import constants
from integrations.wati.services import wati_service
from crater.creator import public as creator_public


LOGGER = logging.getLogger(__name__)


def send_welcome_crater_whatsapp(user):
    """Sending welcome message to people who
        join Crater.

    Args:
        user(User): User who has signed up on crater.

    """
    return wati_service.send_template_message(
        user=user,
        template_name=constants.CRATER_WELCOME_TEMPLATE,
        template_data=[]
    )


def send_stream_reminder_messages_for_group(group):
    followers = []
    host = group.host
    creator = creator_public.get_creator_for_user(host)

    if creator:
        # Add users followers if creator is present.
        followers = creator.followers.filter(notify=True)

    # Get attendees for the group.
    attendees = group.attendees.all()
    # This is the list that has followed the creator but not
    # rsvp'd to the stream.
    only_followers_list = list(set(followers) - set(attendees))
    # Send follower message to followers, and reminder message to attendees.
    send_stream_reminder_messages_for_followers(only_followers_list, group)
    send_stream_reminder_messages_for_attendees(attendees, group)


def send_stream_reminder_messages_for_followers(followers, group):
    """Send stream reminder message to a user for stream.

    Args:
        followers(Queryset(Users)): User who we are sending whatsapp reminder
            to and are follower of the creator doing the stream.
        group(Group): Stream we are sending reminder for.

    """
    creator_name = group.host.display_name
    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        LOGGER.error("Topic image unavailable: {}".format(group.id))
        topic_image_url = ""

    stream_title = group.topic.name
    receivers = []
    for user in followers:
        if not user.get_phone_number():
            continue
        data = {
            "whatsappNumber": user.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "creator_name", "value": creator_name},
                {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
                {"name": "stream_title", "value": stream_title},
                {"name": "session_id", "value": group.id}
            ]
        }
        receivers.append(data)

    return wati_service.send_template_messages(
        template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE,
        receivers=receivers,
        broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE + "_{}".format(group.id)
    )


def send_stream_reminder_messages_for_attendees(users, group):
    """Send stream reminder message to a user for stream.

    Args:
        users(Queryset(Users)): User who we are sending whatsapp reminder
            to.
        group(Group): Stream we are sending reminder for.

    """
    creator_name = group.host.display_name
    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        LOGGER.error("Topic image unavailable: {}".format(group.id))
        topic_image_url = ""

    receivers = []
    for user in users:
        if not user.get_phone_number():
            continue
        data = {
            "whatsappNumber": user.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "creator_name", "value": creator_name},
                {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
                {"name": "session_id", "value": group.id}
            ]
        }
        receivers.append(data)

    return wati_service.send_template_messages(
        template_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE,
        receivers=receivers,
        broadcast_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE + "_{}".format(group.id)
    )


def send_stream_reminder_message_to_attendee(user, group):
    """Send stream reminder message to a user for stream.

    Args:
        user(User): User who we are sending whatsapp reminder
            to.
        group(Group): Stream we are sending reminder for.

    """
    creator_name = group.host.display_name
    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        return LOGGER.error("Topic image unavailable: {}".format(group.id))

    template_data = [
        {"name": "stream_image", "value": topic_image_url},
        {"name": "creator_name", "value": creator_name},
        {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
        {"name": "session_id", "value": group.id}
    ]

    return wati_service.send_template_message(
        user=user,
        broadcast_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE + "_{}".format(group.id),
        template_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE,
        template_data=template_data
    )
