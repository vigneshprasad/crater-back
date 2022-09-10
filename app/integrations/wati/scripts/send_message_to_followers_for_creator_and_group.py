from django.conf import settings
from django.contrib.auth import get_user_model

from conversations import public as conversation_public
from conversations import constants as conversation_constants
from integrations.freshchat import constants as freshchat_constants, freshchat_service
from integrations.wati import constants, private
from integrations.wati.services import wati_service_8953

WATI_8953 = 1
FRESHCHAT = 2


def send_message_for_creator_and_group(
        group,
        creator,
        followers=None,
        account=WATI_8953,
        dry_run=True
):
    # Add users followers if creator is present.
    creator_followers_user_ids = creator.followers.filter(notify=True).values_list("user_id", flat=True)
    creator_followers = list(get_user_model().objects.filter(pk__in=creator_followers_user_ids)) if not followers else followers
    # Remove all attendees from the meeting.
    creator_followers_with_one_plus_stream = []
    creator_followers = set(creator_followers) - set(group.attendees.all())
    for follower in creator_followers:
        streams_watched = follower.dyte_participant.filter(
            dyte_meeting__group__type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
            last_online_at__isnull=False
        ).count()
        if not streams_watched:
            continue
        creator_followers_with_one_plus_stream.append(follower)
    print("Creator: {}".format(creator))
    print("Creator followers count: {}".format(len(creator_followers_with_one_plus_stream)))
    print("Sending follower message for group: {}".format(group))

    if account == WATI_8953:

        creator_name = creator.user.display_name
        try:
            topic_image_url = group.topic.image.url
            # Attach the ACL
            if settings.AWS_DEFAULT_OBJECT_URL not in topic_image_url:
                topic_image_url = settings.AWS_DEFAULT_OBJECT_URL + topic_image_url
        except (ValueError, AttributeError) as e:
            topic_image_url = ""

        stream_title = group.topic.name
        receivers = []
        for follower in creator_followers_with_one_plus_stream:
            # Check if we can send whatsapp to this user.
            if not private.can_send_whatsapp_for_user(follower):
                continue

            data = {
                "whatsappNumber": follower.get_phone_number(),
                "customParams": [
                    {"name": "stream_image", "value": topic_image_url},
                    {"name": "creator_name", "value": creator_name},
                    {"name": "stream_title", "value": stream_title},
                    {"name": "1", "value": group.id}
                ]
            }
            receivers.append(data)

        if not receivers:
            return False

        print("Receivers data")
        print(receivers)

        print("Sending messages to all users from WATI_8953")
        if not dry_run:
            wati_service_8953.send_template_messages(
                template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE_8953,
                receivers=receivers,
                broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE_8953 + "_{}_{}".format(
                    creator_name,
                    group.id
                )
            )
            print("Messages sent to all users from WATI_8953")
    elif account == FRESHCHAT:

        for user in creator_followers_with_one_plus_stream:
            attendee_name = user.get_display_first_name()
            creator_name = creator.user.display_name

            if not attendee_name:
                # Not throwing error since we can't fix
                # this without user input.
                attendee_name = freshchat_constants.PLACEHOLDER_NAME_FOR_WHATSAPP

            topic_name = group.topic.name
            stream_link = conversation_public.get_livestream_link_for_webinar(group)

            data_2 = freshchat_constants.DATA_2_FOR_ATTENDEE_REMINDER.format(
                creator_name=creator_name,
                topic_name=topic_name,
                start_time=group.get_display_start_time()
            )
            data_3 = freshchat_constants.DATA_3_FOR_ATTENDEE_REMINDER.format(
                minutes_remaining=freshchat_constants.WEBINAR_ATTENDEE_REMINDER_DELAY_STR,
                stream_link=stream_link
            )

            print("Template data")
            print([{"data": attendee_name}, {"data": data_2}, {"data": data_3}])

            print("Sending message to {} from Freshchat".format(user))
            if not dry_run:
                freshchat_service.freshchat_whatsapp_service.send_outbound_message(
                    user=user,
                    template_name=freshchat_constants.WEBINAR_ATTENDEE_REMINDER_TEMPLATE,
                    template_data=[
                        {"data": attendee_name},
                        {"data": data_2},
                        {"data": data_3}
                    ]
                )
                print("Sent message to {}".format(user))

            print("-"*10)
