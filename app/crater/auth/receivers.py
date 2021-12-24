from django.dispatch import receiver

from crater.auth import tasks
from users import signals as user_signals


@receiver(user_signals.user_name_populated)
def send_welcome_crater_whatsapp(sender, user, *args, **kwargs):
    """Send crater welcome message on user's name population.

    Args:
        sender(User class): User class.
        user(User): User whose name got populated.

    """
    tasks.send_welcome_crater_whatsapp.apply_async(
        args=(user.pk,),
        countdown=300
    )
