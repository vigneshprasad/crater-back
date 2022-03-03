from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import transaction

from users import constants
from users import signals


@transaction.atomic
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

    # Setting phone number for the user if phone number
    # is not present.
    if not user.get_phone_number():
        user.phone_number = phone_number
        user.save()

    # Mark the user's phone number as verified.
    user.set_phone_number_verified()

    if created:
        # Send a signal on user creation.
        signals.user_created.send(
            sender=user.__class__,
            user=user
        )

    return user, created


def get_user(phone_number):
    """Return user if present.

    Args:
        phone_number(str): String representation of the user's
            phone number.

    """
    try:
        user = get_user_model().objects.get(
            username=phone_number,
            phone_number=phone_number
        )
    except get_user_model().DoesNotExist:
        return None
    except get_user_model().MutipleObjectsReturned:
        raise Exception

    return user


def create_user(phone_number, email, name):
    """Create a user.

    Args:
        phone_number(str): Phone number of the user we are adding.
        email(str): Email ID of the user.
        name(str): User's name

    """
    try:
        user = get_user_model().objects.create(
            username=phone_number,
            phone_number=phone_number,
            email=email
        )
    except Exception as e:
        raise e

    # Set user's name.
    user.set_name(name)

    # Add user to crater club group.
    crater_club_group, _ = Group.objects.get_or_create(
        name=constants.CRATER_CLUB_GROUP
    )
    user.groups.add(crater_club_group)

    return user
