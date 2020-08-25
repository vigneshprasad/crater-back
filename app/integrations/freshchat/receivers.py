from django.dispatch import receiver

from users import signals as user_signals
from integrations.freshchat import tasks


@receiver(user_signals.user_updated)
def create_or_update_freshchat_user(sender, user, *args, **kwargs):
    """Creates or Updates freshchat user if the user is updated
        on our end.

    """
    if not hasattr(user, 'profile'):
        return

    tasks.create_or_update_freshchat_user.delay(user)
