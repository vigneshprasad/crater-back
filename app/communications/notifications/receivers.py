import datetime
import logging

from django.dispatch import receiver

from conversations import signals as conversation_signals
from conversations import models as conversation_models
from users import models as user_models
from communications.notifications import models
from communications.notifications import constants
from communications.notifications import private


@receiver(conversation_signals.conversation_approved)
@receiver(conversation_signals.conversation_created)
def send_notification_to_eligible_users(sender, group, *args, **kwargs):
    """Sends notifications to eligible user when a group is created.

    Args:
        sender(Group Class): Group class representation.
        group(Group): Group object that was created.

    """
    group_host = group.host
    # If there is no group host don't send notifications. That group
    # is either backend created, or manual created.
    if not group_host:
        return

    if not group.is_approved:
        return

    group_host_profile = group_host.profile if group_host.has_profile else None

    if not (group_host and group_host_profile):
        logging.info("Group has no host or host profile: {}".format(group.id))
        return

    min_score = group_host.score
    max_score = min_score + (min_score * 0.3)

    # Getting the notification that has to be sent.
    conversation_create_notification = models.Notification.objects.get(name=constants.GROUP_CONVERSATION_INVITE)

    group_start = group.start
    # Groups that start at the same time as the group created.
    groups_with_same_start = conversation_models.Group.objects.filter(start=group_start)

    # Initial set of eligible users. Only based on score of the user.
    eligible_users = user_models.User.objects.filter(
        score__gte=min_score,
        score__lte=max_score
    )

    final_eligible_users = []
    now_time = datetime.datetime.now()

    for user in eligible_users:
        # Remove user with groups at the same time as the group created.
        if groups_with_same_start.filter(speakers=user):
            continue

        notifications_sent = models.NotificationLog.objects.filter(
            user=user,
            notification=conversation_create_notification,
            created_at__year=now_time.year,
            created_at__month=now_time.month,
            created_at__day=now_time.day,
        )
        # Remove user to whom 4 notifications have gone out today for
        # conversation creation.
        if notifications_sent.count() >= 4:
            continue

        final_eligible_users.append(user)

    final_eligible_user_ids = [user.pk for user in final_eligible_users]

    # Get user data needed for notification.
    tag_name = group_host_profile.new_tag.first().name if group_host_profile.new_tag.first() else "Professional"
    year_of_experience = group_host_profile.years_of_experience or 1
    year_of_experience_str = dict(user_models.Profile.YEARS_OF_EXPERIENCE_CHOICES).get(
        year_of_experience
    )

    # Get the notification json and append variables to it.
    notification_json = private.create_notification_json_from_notification(conversation_create_notification)
    notification_json["headings"]["en"] = notification_json["headings"]["en"].format(
        time=group.get_display_start_time(), topic=group.topic.name
    )
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(
        first_name=group_host.get_display_first_name(),
        new_tag=tag_name,
        years_of_experience=year_of_experience_str
    )
    # Get data for the notification.
    data = {
        "obj_type": conversation_create_notification.obj_type,
        "group_id": group.id
    }
    private.send_bulk_notifications.delay(final_eligible_user_ids, notification_json, data=data)
    private.create_notification_logs(final_eligible_users, conversation_create_notification, notification_json, data=data)
