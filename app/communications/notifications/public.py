import logging

from django.contrib.auth import get_user_model

from communications.notifications import models, constants, private
from crater.creator import public as creator_public
from conversations import constants as conversation_constants


def send_conversation_create_notification_for_group(group):
    """Sends notification to all users in a group."""
    users = group.speakers.all()
    for user in users:
        send_conversation_created_notification(user, group)


def send_conversation_created_notification(user, group):
    """Sends notification for conversation created.

     Args:
         user(User): User to whom we are sending the notification.
         group(Group): Group the user is associated with.

     """
    # TODO(Nishant): Use this is group creation script.
    notification = models.Notification.objects.filter(
        name=constants.GROUP_CONVERSATION_CREATED,
        is_active=True
    ).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.GROUP_CONVERSATION_CREATED))
        return

    # Get the notification json and append variables to it.
    notification_json = private.create_notification_json_from_notification(notification)
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(time=group.get_display_start_time(), day=group.get_display_day())
    # Get data for the notification.
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id
    }
    private.send_notification.delay(user.pk, notification_json, data=data)
    private.create_notification_log(user, notification, notification_json, data=data)


def send_optin_notifications_for_users(users=None):
    """Wrapper to send notification to multiple users.

    Args:
        users(List(User)): List of users we want to send
            optin notifications.

    """
    if not users:
        return False

    for user in users:
        send_optin_notifications(user)


def send_optin_notifications(user):
    """Sends notification for conversation created.

     Args:
         user(User): User to whom we are sending the notification.

     """
    # TODO(Nishant): Add this to sunday script for optin.
    notification = models.Notification.objects.filter(
        name=constants.OPTIN_NOTIFICATION,
        is_active=True
    ).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.OPTIN_NOTIFICATION))
        return

    # Create notification json and data.
    notification_json = private.create_notification_json_from_notification(notification)
    data = {
        "obj_type": constants.OBJECT_TYPE_CREATE_CONVERSATION
    }
    private.send_notification.delay(user.pk, notification_json, data=data)
    private.create_notification_log(user, notification, notification_json, data=data)


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
        logging.error("Notification not present: {}".format(constants.STREAM_REMINDER_NOTIFICATION_ATTENDEE))
        return False

    attendees = group.attendees.all()
    attendee_pks = attendees.values_list("pk", flat=True)

    notification_json = private.create_notification_json_from_notification(attendee_reminder_notification)
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
        time=group.get_display_start_time(), topic=group.topic.name)
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id,
        "auto_connect": False
    }
    # Can only send if the notification doesn't change between each user.
    private.send_bulk_notifications(user_pks=attendee_pks, notification_json=notification_json, data=data)
    private.create_notification_logs(
        users=attendees,
        notification=attendee_reminder_notification,
        notification_json=notification_json,
        data=data
    )
    logging.info("Sent reminder to attendees: {}".format(group.id))

    # For per user notification send, use this code block.
    # for attendee in attendees:
    #     notification_json = private.create_notification_json_from_notification(notification)
    #     notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
    #         time=group.get_display_start_time(), topic=group.topic.name)
    #     data = {
    #         "obj_type": constants.OBJECT_TYPE_CONVERSATION,
    #         "group_id": group.id,
    #         "auto_connect": False
    #     }
    #     private.send_notification.delay(attendee.pk, notification_json, data=data)
    #     private.create_notification_log(attendee, notification, notification_json, data=data)

    users_to_exclude = attendees
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
    logging.info("Sent notification reminder to host followers: {}".format(group.id))

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
        logging.info("Sent notification reminder to co-hosts followers: {} - {}".format(
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
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
        time=group.get_display_start_time(), topic=group.topic.name
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
        notification_json=notification_json,
        data=data
    )
    private.create_notification_logs(
        users=followers,
        notification=follower_reminder_notification,
        notification_json=notification_json,
        data=data
    )


def send_reminder_notifications_for_user_and_stream(user, group):
    """Send reminder notification for a user and a group.

    Args:
        user(User): User we are sending the notification to.
        group(Group): Group we are sending the reminder for.

    """
    stream_reminder_notification = models.Notification.objects.filter(
        name=constants.STREAM_REMINDER_NOTIFICATION_ATTENDEE,
        is_active=True
    ).first()

    if not stream_reminder_notification:
        logging.error("Notification not present: {}".format(constants.STREAM_REMINDER_NOTIFICATION_ATTENDEE))
        return False

    # Get the notification json and append variables to it.
    stream_reminder_notification_json = private.create_notification_json_from_notification(stream_reminder_notification)
    # TODO(Nishant): Add the contents here.
    stream_reminder_notification_json["contents"]["en"] = stream_reminder_notification_json["contents"]["en"].format(
        time=group.get_display_start_time(),
        day=group.get_display_day()
    )
    # Get data for the notification.
    data = {
        "obj_type": constants.OBJECT_TYPE_STREAM,
        "group_id": group.id,
        "auto_connect": True
    }

    # TODO(Nishant): Check if we can convert this to bulk notifications.
    private.send_notification.delay(user.pk, stream_reminder_notification_json, data=data)
    private.create_notification_log(
        user,
        stream_reminder_notification,
        stream_reminder_notification_json,
        data=data
    )
