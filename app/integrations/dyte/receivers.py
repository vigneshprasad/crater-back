from django.dispatch import receiver

from conversations import signals as conversation_signals
from integrations.dyte.service import dyte_service


@receiver(conversation_signals.webinar_created)
def create_dyte_meeting_for_webinar(sender, group, *args, **kwargs):
    """Create a dyte meeting for webinar on Group creation.

    Args:
        sender(Group class): Class object for group.
        group(Group): Webinar group we are creating dyte meeting
            for.

    """
    dyte_service.create_webinar(group)
