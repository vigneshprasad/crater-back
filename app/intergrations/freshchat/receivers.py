from django.dispatch import receiver

from users import signals as user_signals
from intergrations.freshchat import _freshchat_service


@receiver(user_signals.user_updated)
def create_or_update_freshchat_user(sender, user, *args, **kwargs):
    if not hasattr('profile', user):
        return
    _freshchat_service.freshchat_whatsapp_service.create_or_update_user(
        user
    )
