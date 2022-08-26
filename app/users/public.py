from urllib.request import urlopen

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction

from users import constants
from users import models
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

    # Create profile with the user object.
    profile, profile_created = models.Profile.objects.get_or_create(
        user=user
    )

    # Setting phone number for the user if phone number
    # is not present.
    if not user.get_phone_number():
        user.phone_number = phone_number
        user.save()

    # Mark the user's phone number as verified.
    user.set_phone_number_verified()

    if created or (not user.has_profile):
        # Send a signal on user creation, or if the
        # user has no profile.
        signals.user_created.send(
            sender=user.__class__,
            user=user
        )

    return user, created


def get_user_for_phone_number(phone_number):
    """Return user if present.

    Args:
        phone_number(str): String representation of the user's
            phone number.

    """
    try:
        user = get_user_model().objects.get(username=phone_number)
    except get_user_model().DoesNotExist:
        return None
    except get_user_model().MutipleObjectsReturned:
        raise Exception

    return user


def get_user_for_email(email):
    """Return user if present.

    Args:
        email(str): String representation of the user's
            email.

    """
    try:
        user = get_user_model().objects.get(email=email)
    except get_user_model().DoesNotExist:
        return None
    except get_user_model().MutipleObjectsReturned:
        raise Exception

    return user


def create_user(
        phone_number,
        email,
        name,
        primary_url=None,
        profile_image_name=None,
        profile_image_url=None,
        profile_introduction=None,
):
    """Create a user.

    Args:
        phone_number(str): Phone number of the user we are adding.
        email(str): Email ID of the user.
        name(str): User's name
        primary_url(str): Primary url for the user.
        profile_image_name(str): Profile image name.
        profile_image_url(str): Profile image url.
        profile_introduction(str): Profile introduction.

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

    # Refresh user from DB.
    user.refresh_from_db()

    # Get or create profile for user.
    profile, _ = models.Profile.objects.get_or_create(
        user=user
    )
    profile.primary_url = primary_url
    profile.introduction = profile_introduction
    profile.save()

    if profile_image_name and profile_image_url:
        # Get the image file from the url and save it as
        # image object.
        image_temp = NamedTemporaryFile()
        image_temp.write(urlopen(profile_image_url).read())
        image_temp.flush()

        # This will generate proper image.url as well.
        profile.photo.save(profile_image_name, File(image_temp))
        profile.save()

    # Raising user created here.
    signals.user_created.send(
        sender=user.__class__,
        user=user
    )

    return user
