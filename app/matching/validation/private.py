import re
import urllib.parse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from devices import public as devices_public
from matching.validation import models
from matching.validation import constants


def validate_user(user):
    pass


def validate_based_on_phone_price(user):
    user_device = devices_public.get_device_info_for_user(user)
    if not user_device:
        return

    user_device_price = user_device.get("device_price")
    user_score = user.score

    validation = None

    if user_score >= 50 and user_device_price <= 20000:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.PHONE_PRICE_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
    elif user_score <= 40 and user_device_price <= 50000:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.PHONE_PRICE_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_LOW_ENUM
            }
        )

    return validation


def validate_based_on_introduction(user):
    pass


def validate_based_on_education(user):
    pass


def validate_based_on_linkedin_url(user):
    """Validate a user based on linkedin url provided by the user.

    Args:
        user(User): User we are validating based on linkedin url.

    """
    if not user.has_profile:
        return

    validation = None

    profile = user.profile
    linkedin_url = profile.linkedin_url

    if not linkedin_url:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.LINKEDIN_URL_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        return validation

    if not _validate_linkedin_profile_url(linkedin_url):
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.LINKEDIN_URL_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )

    return validation


def _validate_linkedin_profile_url(url):
    """Returns if the linkedin profile url is valid.

    Args:
        url(str): Url for linkedin public profile.

    """

    # Check if the provided value is a valid url.
    try:
        validate = URLValidator()
        validate(url)
    except ValidationError:
        return False

    try:
        parser = urllib.parse.urlparse(url)
    except AttributeError:
        return False

    # Get the network location and path of the url.
    url_netloc = parser.netloc
    url_path = parser.path

    if url_netloc and url_netloc.lower() in constants.VALID_LINKEDIN_LOCATION_URLS:
        return True

    if url_path.lower() in constants.VALID_LINKEDIN_LOCATION_URLS:
        return True

    return False
