from django.contrib.auth import get_user_model

from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import models as creator_models, public as creator_public
from integrations.wati import constants
from integrations.wati.services import wati_service_8953


def run(phone_number_list, dry_run=True):
    """Send message to phone numbers outside of Crater.

    Args:
        phone_number_list(list): List of phone numbers we are sending
            the message to
        dry_run(bool): Is the script in dry or real run.

    """
    if not phone_number_list:
        return

    print(len(phone_number_list))
    creators = creator_models.Creator.objects.filter(
        user__username__in=phone_number_list
    )
    print(creators.count())
    receivers = []

    for creator in creators:
        creator_name = creator.user.display_name
        creator_groups = conversation_models.Group.objects.filter(
            host=creator.user,
            type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM
        )
        last_group = creator_groups.first()
        if not last_group:
            last_group = conversation_models.Group.objects.filter(
                speakers=creator.user,
                type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM
            ).first()

        if not last_group:
            print("Group doesn't exist for: {}".format(creator.user.get_phone_number()))
            print("******")
            continue

        # follower_count = creator_models.Follower.objects.filter(creator=creator).count()
        subscriber_count = creator_public.get_subscriber_count_for_creator(creator) + 50
        subscriber_count_str = "{}+".format(subscriber_count)
        users_since_last_stream = get_user_model().objects.filter(date_joined__gte=last_group.start).count() + 50000
        streams_since_last_stream = conversation_models.Group.objects.filter(start__gt=last_group.start).count() + 2000
        streams_since_last_stream_str = "{}+".format(streams_since_last_stream)

        # Print all the data.
        print("Creator Name: {}".format(creator_name))
        print("Creator Number: {}".format(creator.user.get_phone_number()))
        print("ID: {}".format(last_group.id), "-", "Last stream date: {}".format(last_group.get_display_start()))
        # print("Follower Count: {}".format(follower_count))
        print("Subscriber Count: {}".format(subscriber_count_str))
        print("Users since last streamed: {}".format(users_since_last_stream))
        print("Streams since last streamed: {}".format(streams_since_last_stream_str))

        data = {
            "whatsappNumber": creator.user.get_phone_number(),
            "customParams": [
                {"name": "creator_name", "value": creator_name},
                {"name": "subscribers_count", "value": subscriber_count_str},
                {"name": "user_count", "value": users_since_last_stream},
                {"name": "stream_count", "value": streams_since_last_stream_str},
            ]
        }
        receivers.append(data)
        print("******")

    if not receivers:
        return

    print("Sending messages to {} numbers".format(len(receivers)))
    # print("Receivers data")
    # print(receivers)

    if not dry_run:
        print("Sending messages")
        response = wati_service_8953.send_template_messages(
            template_name=constants.CREATOR_REACTIVE_PROFILE_8953,
            receivers=receivers,
            broadcast_name=constants.CREATOR_REACTIVE_PROFILE_8953
        )

        print(response)
        print("Sent reminder message")
