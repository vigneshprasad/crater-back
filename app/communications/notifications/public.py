import logging

from django.contrib.auth import get_user_model

from communications.notifications import models, constants, private
from crater.creator import public as creator_public
from conversations import constants as conversation_constants


LOGGER = logging.getLogger(__name__)


def send_reminder_notifications_for_stream(group):
    """Send reminder notification to attendees and followers
        of a group.

    Args:
        group(Group): Group we are sending reminder notifications for.

    """
    attendee_reminder_notification = models.Notification.objects.filter(
        name=constants.STREAM_REMINDER_NOTIFICATION_ATTENDEE
    ).first()

    if not attendee_reminder_notification:
        LOGGER.error("Notification not present: {}".format(constants.STREAM_REMINDER_NOTIFICATION_ATTENDEE))
        return False

    attendees = group.attendees.all()
    attendee_pks = attendees.values_list("pk", flat=True)

    notification_json = private.create_notification_json_from_notification(attendee_reminder_notification)
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
        topic_name=group.topic.name.title()
    )
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id,
        "auto_connect": False
    }
    # Can only send if the notification doesn't change between each user.
    private.send_bulk_notifications(
        user_pks=attendee_pks,
        notification_id=attendee_reminder_notification.id,
        notification_json=notification_json,
        data=data,
    )
    LOGGER.info("Sent reminder to attendees: {}".format(group.id))

    # If it's a private stream don't send reminder to followers.
    if group.privacy == conversation_constants.GROUP_PRIVACY_PRIVATE_ENUM:
        return

    users_to_exclude = list(attendees)
    host = group.host
    creator = creator_public.get_creator_for_user(host)
    host_followers = []

    if creator:
        # Add users followers if creator is present.
        host_followers_user_ids = creator.followers.filter(notify=True).values_list("user_id", flat=True)
        host_followers = list(get_user_model().objects.filter(pk__in=host_followers_user_ids))

    # This is the list that has followed the creator but not
    # rsvp'd to the stream.
    host_followers_list = list(set(host_followers) - set(users_to_exclude))
    host_followers_list_with_one_plus_streams = []
    users_to_exclude += host_followers

    # Filter out followers who have watched two plus streams.
    for follower in host_followers_list:
        streams_watched = follower.dyte_participant.filter(
            dyte_meeting__group__type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
            last_online_at__isnull=False
        ).count()
        if not streams_watched:
            continue
        host_followers_list_with_one_plus_streams.append(follower)

    # Send follower message to host followers.
    send_reminder_notification_for_stream_followers(
        group,
        host_followers_list_with_one_plus_streams,
        creator=creator
    )
    LOGGER.info("Sent notification reminder to host followers: {}".format(group.id))

    speakers = group.speakers.all().exclude(pk=host.pk)
    speaker_creators = []

    for speaker in speakers:
        speaker_creator = creator_public.get_creator_for_user(speaker)
        if not speaker_creator:
            continue
        speaker_creators.append(speaker_creator)

    for speaker_creator in speaker_creators:
        speaker_follower_user_ids = speaker_creator.followers.filter(
            notify=True
        ).values_list("user_id", flat=True)
        speaker_followers = list(get_user_model().objects.filter(pk__in=speaker_follower_user_ids))
        # This is the list that has followed the creator but not
        # rsvp'd to the stream.
        speaker_followers_list = list(set(speaker_followers) - set(users_to_exclude))
        speaker_followers_list_with_one_plus_streams = []
        # Filter out followers who have watched two plus streams.
        users_to_exclude += speaker_followers
        for follower in speaker_followers_list:
            streams_watched = follower.dyte_participant.filter(
                dyte_meeting__group__type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
                last_online_at__isnull=False
            ).count()
            if not streams_watched:
                continue
            speaker_followers_list_with_one_plus_streams.append(follower)

        # Send stream reminder to speakers/co-host followers.
        send_reminder_notification_for_stream_followers(
            group,
            speaker_followers_list_with_one_plus_streams,
            creator=speaker_creator
        )
        LOGGER.info("Sent notification reminder to co-hosts followers: {} - {}".format(
            group.id,
            speaker_creator
        ))


def send_reminder_notification_for_stream_followers(group, followers, creator=None):
    """Send stream reminder message to a user for stream.

    Args:
        followers(Queryset(Users)): User who we are sending
            whatsapp reminder to and are follower of the
            creator doing the stream.
        group(Group): Stream we are sending reminder for.
        creator(Creator): Creator whose followers we are sending
            message to.

    """
    host = group.host
    creator = creator if creator else creator_public.get_creator_for_user(host)
    if not creator:
        return False

    follower_reminder_notification = models.Notification.objects.filter(
        name=constants.STREAM_REMINDER_NOTIFICATION_FOLLOWER).first()

    if not follower_reminder_notification:
        logging.error("Notification not present: {}".format(constants.STREAM_REMINDER_NOTIFICATION_FOLLOWER))
        return False

    notification_json = private.create_notification_json_from_notification(follower_reminder_notification)
    notification_json["headings"]["en"] = notification_json["headings"]["en"].format(
        creator_name=host.display_name
    )
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
        topic_name=group.topic.name.title()
    )
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id,
        "auto_connect": False
    }
    # Can only send if the notification doesn't change between each user.
    follower_pks = [follower.pk for follower in followers]

    private.send_bulk_notifications(
        user_pks=follower_pks,
        notification_id=follower_reminder_notification.id,
        notification_json=notification_json,
        data=data
    )
