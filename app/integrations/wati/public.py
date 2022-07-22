import logging

from django.contrib.auth import get_user_model

from conversations import constants as conversation_constants
from crater.creator import public as creator_public
from integrations.wati import constants, private
from integrations.wati.services import wati_service_9051
from integrations.wati.services import wati_service_8953

LOGGER = logging.getLogger(__name__)


def send_welcome_crater_whatsapp(user, account=constants.WATI_9051_ACCOUNT_ENUM):
    """Sending welcome message to people who
        join Crater.

    Args:
        user(User): User who has signed up on crater.
        account(int): Which account to send the whatsapp from.

    """
    if account == constants.WATI_9051_ACCOUNT_ENUM:
        return wati_service_9051.send_template_message(
            user=user,
            template_name=constants.CRATER_WELCOME_TEMPLATE,
            template_data=[]
        )
    elif account == constants.WATI_8953_ACCOUNT_ENUM:
        return wati_service_8953.send_template_message(
            user=user,
            template_name=constants.CRATER_WELCOME_TEMPLATE,
            template_data=[]
        )


def send_stream_reminder_to_group_host(
        group,
        account=constants.WATI_9051_ACCOUNT_ENUM
):
    """Send reminder message to host of the
        stream.

    Args:
        group(Group): Stream we are sending reminders for.
        account(int): Which account to send the whatsapp from.

    """
    host = group.host
    if not host:
        return

    host_name = host.get_display_first_name()

    poc_name = constants.DEFAULT_POC_NAME
    poc_number = constants.DEFAULT_POC_NUMBER

    # Get actual POC details if exists.
    if host.is_creator:
        creator = host.creator
        creator_poc = creator.point_of_contact
        if creator_poc:
            poc_name = creator_poc.get_display_first_name()
            poc_number = creator_poc.get_phone_number()

    template_data = [
        {"name": host_name},
        {"session_id": group.id},
        {"start_time": group.get_display_start_time()},
        {"poc_name": poc_name},
        {"poc_number": poc_number},
    ]

    if account == constants.WATI_9051_ACCOUNT_ENUM:
        return wati_service_9051.send_template_message(
            user=host,
            template_name=constants.CREATOR_REMINDER_TEMPLATE,
            template_data=template_data
        )
    elif account == constants.WATI_8953_ACCOUNT_ENUM:
        return wati_service_8953.send_template_message(
            user=host,
            template_name=constants.CREATOR_REMINDER_TEMPLATE,
            template_data=template_data
        )


def send_stream_reminder_messages_for_group(
        group,
        attendee_account=constants.WATI_9051_ACCOUNT_ENUM,
        follower_account=constants.WATI_9051_ACCOUNT_ENUM
):
    """Send reminder message to attendees and followers of the
        creator doing the stream.

    Args:
        group(Group): Stream we are sending reminders for.
        attendee_account(int): Which account to send the attendee reminder from.
        follower_account(int): Which account to send the follower reminder from.

    """
    followers = []
    host = group.host
    creator = creator_public.get_creator_for_user(host)

    if creator:
        # Add users followers if creator is present.
        user_ids = creator.followers.filter(notify=True).values_list("user_id", flat=True)
        followers = get_user_model().objects.filter(pk__in=user_ids)

    # Get attendees for the group.
    attendees = group.attendees.all()
    # This is the list that has followed the creator but not
    # rsvp'd to the stream.
    followers_list = list(set(followers) - set(attendees))
    followers_list_with_one_plus_streams = []

    # Filter out followers who have watched two plus streams.
    for follower in followers_list:
        streams_watched = follower.dyte_participant.filter(
            dyte_meeting__group__type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
            last_online_at__isnull=False
        ).count()
        if not streams_watched:
            continue
        followers_list_with_one_plus_streams.append(follower)

    # Send follower message to followers.
    send_stream_reminder_messages_for_followers(
        followers_list_with_one_plus_streams,
        group,
        account=follower_account
    )
    # Send reminder message to attendees.
    send_stream_reminder_messages_for_attendees(
        attendees,
        group,
        account=attendee_account
    )


def send_stream_reminder_messages_for_followers(followers, group, account=constants.WATI_9051_ACCOUNT_ENUM):
    """Send stream reminder message to a user for stream.

    Args:
        followers(Queryset(Users)): User who we are sending whatsapp reminder
            to and are follower of the creator doing the stream.
        group(Group): Stream we are sending reminder for.
        account(int): Which account to send the whatsapp from.

    """
    if not followers:
        return

    creator_name = group.host.display_name
    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        LOGGER.error("Topic image unavailable: {}".format(group.id))
        topic_image_url = ""

    stream_title = group.topic.name
    receivers = []
    for follower in followers:
        # Check if we can send whatsapp to this user.
        if not private.can_send_whatsapp_for_user(follower):
            continue

        data = {
            "whatsappNumber": follower.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "creator_name", "value": creator_name},
                {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
                {"name": "stream_title", "value": stream_title},
                {"name": "session_id", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return

    if account == constants.WATI_9051_ACCOUNT_ENUM:
        return wati_service_9051.send_template_messages(
            template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE,
            receivers=receivers,
            broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE + "_{}".format(group.id)
        )
    elif account == constants.WATI_8953_ACCOUNT_ENUM:
        return wati_service_8953.send_template_messages(
            template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE,
            receivers=receivers,
            broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE + "_{}".format(group.id)
        )


def send_stream_reminder_messages_for_attendees(attendees, group, account=constants.WATI_9051_ACCOUNT_ENUM):
    """Send stream reminder message to a user for stream.

    Args:
        attendees(Queryset(Users)): User who we are sending whatsapp reminder
            to.
        group(Group): Stream we are sending reminder for.
        account(int): Which account to send the whatsapp from.

    """
    if not attendees:
        return

    creator_name = group.host.display_name
    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        LOGGER.error("Topic image unavailable: {}".format(group.id))
        topic_image_url = ""

    receivers = []
    for attendee in attendees:
        # Check if we can send whatsapp to this user.
        if not private.can_send_whatsapp_for_user(attendee):
            continue

        data = {
            "whatsappNumber": attendee.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "creator_name", "value": creator_name},
                {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
                {"name": "session_id", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return

    if account == constants.WATI_9051_ACCOUNT_ENUM:
        return wati_service_9051.send_template_messages(
            template_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE,
            receivers=receivers,
            broadcast_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE + "_{}".format(group.id)
        )
    elif account == constants.WATI_8953_ACCOUNT_ENUM:
        return wati_service_8953.send_template_messages(
            template_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE,
            receivers=receivers,
            broadcast_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE + "_{}".format(group.id)
        )


# TODO(Sanjeev): Add logic after WATI template is approved.
def send_top_stream_message(stream, user_ids):
    # Filter users
    pass
