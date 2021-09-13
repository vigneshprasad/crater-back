from django.contrib.auth import get_user_model

from users import signals


def get_or_create_user(phone_number):
    """Return user if present or create a new one.

    Args:
        phone_number(str): String representation of the user's
            phone number.

    """
    user, created = get_user_model().objects.get_or_create(
        username=phone_number,
        defaults={
            "phone_number": phone_number
        }
    )

    if created:
        # Send a signal on user creation.
        signals.user_created.send(
            sender=user.__class__,
            user=user
        )

    return user, created
