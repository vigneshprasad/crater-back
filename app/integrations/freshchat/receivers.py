from django.conf import settings
from django.dispatch import receiver

from users import signals as user_signals
from integrations.freshchat import tasks
from integrations.freshchat import public
from resources.meetings import signals as meeting_signals


@receiver(user_signals.user_updated)
def create_or_update_freshchat_user(sender, user, *args, **kwargs):
    """Creates or Updates freshchat user if the user is updated
        on our end.

    """
    if not user.has_profile:
        return

    if not settings.FRESHCHAT_USER_CREATION_ALLOWED:
        return

    tasks.create_or_update_freshchat_user.delay(user.pk)

@receiver(meeting_signals.registered_for_meeting)
def registered_for_meeting(sender, user, **kwargs):
    """
        If a user meeting preference is created
        a whatsapp message is sent to the user 
        with a confirmation
    """

    # Removing signal object from kwargs.
    kwargs.pop('signal')

    created = kwargs.pop('created', None)
     
    if created:
        public.send_registration_confirmation(user)