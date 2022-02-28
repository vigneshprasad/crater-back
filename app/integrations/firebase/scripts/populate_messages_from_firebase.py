import datetime

from django.conf import settings
from django.contrib.auth import get_user_model

from integrations.firebase import service
from conversations import constants as conversation_constants
from conversations import models as conversation_models


firebase_service = service.firebase_service


def run(date, groups=None, dry_run=True):

    groups_after_firebase = conversation_models.Group.objects.filter(
        start__gte=date,
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM
    ) if not groups else groups
    group_collection = firebase_service.db.collection("group")

    total_messages_added = 0
    total_messages_to_be_added = 0
    all_firebase_groups = []

    for group in groups_after_firebase:
        # Get all message collections in group document.
        message_collection = group_collection.document("{}".format(group.id)).collections()

        for message in message_collection:

            for message_data in message.stream():

                print("------")

                # All the data we need to create group message in backend.
                message_dict = message_data.to_dict()
                group_id = message_dict.get("group")
                display_name = message_dict.get("display_name")
                message = message_dict.get("message")
                created_at = message_dict.get("created_at")
                user_pk = message_dict.get("sender")
                firebase_message_id = message_data.id
                message_type = message_dict.get("type")

                # Check if group message exists for firebase_message_id.
                group_message_exists = conversation_models.GroupMessage.objects.filter(
                    firebase_message_id=firebase_message_id
                ).exists()

                # If group_message has been created before continue from there.
                if group_message_exists:
                    continue

                try:
                    user = get_user_model().objects.get(pk=user_pk)
                except get_user_model().DoesNotExist:
                    print("User Pk doesn't exist: {}".format(user_pk))
                    continue

                print("Firebase message ID: ", firebase_message_id)
                print("Group ID: ", group_id)
                print("User: ", user)
                print("Display name: ", display_name)
                print("Message: ", message)
                print("Created at: ", created_at)
                print("Message Type: ", message_type)

                if group_id not in all_firebase_groups:
                    all_firebase_groups.append(group_id)

                total_messages_to_be_added += 1

                if not dry_run:

                    print("Creating group message")
                    group_message, created = conversation_models.GroupMessage.objects.get_or_create(
                        firebase_message_id=firebase_message_id,
                        group_id=group_id,
                        defaults={
                            "message": message,
                            "sender": user,
                            "display_name": display_name,
                            "type": message_type
                        }
                    )

                    if created:
                        # Bypassing auto_add_now on created at using update for queryset.
                        group_message_queryset = conversation_models.GroupMessage.objects.filter(
                            id=group_message.id
                        )
                        print("Group message created: {}".format(group_message.id))
                        print("Group queryset: {}".format(group_message_queryset))
                        # Update created_at to created_at from Firebase.
                        print("Updating created_at")
                        group_message_queryset.update(
                            created_at=created_at
                        )
                        print("Updated created_at")
                        total_messages_added += 1

                print("-------")

    return len(all_firebase_groups), total_messages_to_be_added, total_messages_added
