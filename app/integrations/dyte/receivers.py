from django.dispatch import receiver

from conversations import signals as conversation_signals
from integrations.dyte.service import dyte_service
from integrations.dyte import private


@receiver(conversation_signals.webinar_created)
def create_dyte_meeting_for_webinar(sender, group, *args, **kwargs):
    """Create a dyte meeting for webinar on Group creation.

    Args:
        sender(Group class): Class object for group.
        group(Group): Webinar group we are creating dyte meeting
            for.

    """
    dyte_service.create_webinar(group)


@receiver(conversation_signals.attendees_added_to_group)
def add_participants_to_dyte_meeting(sender, group, users, *args, **kwargs):
    """Add participant to dyte meeting once a attendee is added to the webinar.

    Args:
        sender(Group class): Class object for group.
        group(Group): Webinar group we are creating dyte meeting
            for.
        users(list/queryset): List of queryset of users that got
            added to the group.

    """
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        return False

    for user in users:
        # If the user has already been added as a participant for
        # dyte meeting, don't add again.
        if private.get_dyte_participant_for_user_and_group(user, group):
            continue

        dyte_service.add_participant_to_meeting(dyte_meeting, user)


@receiver(conversation_signals.attendee_added_to_group)
def add_participant_to_dyte_meeting(sender, group, user, *args, **kwargs):
    """Add participant to dyte meeting once a attendee is added to the webinar.

    Args:
        sender(Group class): Class object for group.
        group(Group): Webinar group we are creating dyte meeting
            for.
        user(User): User that got added to the group.

    """
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        return False

    # If the user has already been added as a participant for
    # dyte meeting, don't add again.
    if private.get_dyte_participant_for_user_and_group(user, group):
        return False

    dyte_service.add_participant_to_meeting(dyte_meeting, user)
