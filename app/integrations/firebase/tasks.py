import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from conversations import constants as conversation_constants, models as conversation_models
from integrations.firebase import service

firebase_service = service.firebase_service


@periodic_task(run_every=crontab(hour=18, minute=00))
def populate_message_from_firebase(date=None):
    """Populates messages from firebase to our backend everyday.

    Args:
        date(str): Date string we are adding the messages for.

    """
    if not date:
        today = datetime.date.today()
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time())
        today_end = datetime.datetime.combine(datetime.date.today(), datetime.time(11, 59))
    else:
        today = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        today_start = datetime.datetime.combine(today, datetime.time())
        today_end = datetime.datetime.combine(today, datetime.time(11, 59))

    groups_for_today = conversation_models.Group.objects.filter(
        start__gte=today_start,
        start__lte=today_end,
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM
    )
    group_collection = firebase_service.db.collection("group")

    for group in groups_for_today:
        # Get all message collections in group document.
        message_collection = group_collection.document("{}".format(group.id)).collections()

        for message in message_collection:
            for message_data in message.stream():
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
                    continue
                except ValidationError:
                    continue

                # Create group messages and update the created at.
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
                    group_message.created_at = created_at
                    group_message.save()
