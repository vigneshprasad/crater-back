from django.dispatch import receiver

from conversations import signals as conversation_signals


@receiver(conversation_signals.conversation_approved)
@receiver(conversation_signals.conversation_created)
def send_notification_to_eligible_users(sender, group, *args, **kwargs):
    """Sends notifications to eligible user when a group is created.

    Args:
        sender(Group Class): Group class representation.
        group(Group): Group object that was created.

    """
    return False
