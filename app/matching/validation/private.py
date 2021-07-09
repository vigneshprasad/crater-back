import copy
import re
import urllib.parse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from devices import public as devices_public
from matching.validation import models
from matching.validation import constants
from tags import services as tag_services
from users import choices as user_constants


def get_validation_for_user_and_rule(user, rule):
    """Gets UserValidation object for a user and rule.

    Args:
        user(User): User for which we are getting validations.
        rule(str): Rule for which we are getting the validation.

    """
    try:
        validation = models.UserValidation.objects.get(
            user=user,
            rule=rule
        )
    except models.UserValidation.DoesNotExist:
        validation = None

    return validation


def validate_based_on_phone_price(user):
    """Validate a user based on phone price.

    Args:
        user(User): User we are validating based on phone price..

    """
    validation = get_validation_for_user_and_rule(user, constants.PHONE_PRICE_VALIDATION)

    if validation:
        # If the user's validation failed and is marked as validated manually
        # don't run the validation again.
        if validation.is_validated:
            return

        # Marking the validation object as is_validated True so that if the
        # validation doesn't fail for the user. Validation is passed.
        validation.is_validated = False

    user_device = devices_public.get_device_info_for_user(user)
    # If the user doesn't have device don't run the validation
    if not user_device:
        return False

    user_device_price = user_device.get("device_price")
    user_score = user.score

    # Mark the validation as False if we are updating the
    # Validation object (Failed Validation).
    if user_score >= 50 and user_device_price <= 20000:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.PHONE_PRICE_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    if user_score <= 40 and user_device_price <= 40000:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.PHONE_PRICE_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_LOW_ENUM
            }
        )
        validation.is_validated = False

    # If the validation failed by the rules written, is_validated will be
    # False at this point.
    validation.save()

    return validation


def validate_based_on_introduction(user):
    """Validate a user based on his introduction.

    Args:
        user(User): User we are validating based on his introduction.

    """
    validation = get_validation_for_user_and_rule(user, rule=constants.INTRODUCTION_VALIDATION)

    if validation:
        # If the user's validation failed and is marked as validated manually
        # don't run the validation again.
        if validation.is_validated:
            return

        # Marking the validation object as is_validated True so that if the
        # validation doesn't fail for the user. Validation is passed.
        validation.is_validated = False

    if not user.has_profile:
        return

    introduction = user.profile.get_introduction()
    if not introduction:
        return

    all_words_in_introduction = re.findall(r"\w+|[^\w\s]", introduction, re.UNICODE)
    introduction_word_length = len(all_words_in_introduction)

    # Blacklisted word validation.
    for word in all_words_in_introduction:
        if word.lower() in constants.BLACKLISTED_INTRODUCTION_WORDS:
            validation = models.UserValidation.objects.update_or_create(
                user=user,
                rule=constants.INTRODUCTION_VALIDATION,
                defaults={
                    "result": constants.VALIDATION_SCORE_HIGH_ENUM
                }
            )
            validation.is_validated = False

    # Introduction word count validation.
    if introduction_word_length <= 10:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.INTRODUCTION_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # Email present in introduction validation.
    email_string_in_introduction = re.findall("\S+@\S+", introduction)
    if email_string_in_introduction:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.INTRODUCTION_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # Urls in introduction validation.
    urls = re.findall(constants.REGEX_FOR_URL, introduction)
    if urls:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.INTRODUCTION_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # Special characters, smiley etc. in introduction validation.
    special_characters = []
    for character in introduction:
        if not character.isalnum() and character not in constants.VALID_SPECIAL_CHARACTERS:
            special_characters.append(character)

    if special_characters:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.INTRODUCTION_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # Phone number in introduction validation.
    all_numbers_in_intro = [character for character in all_words_in_introduction if character.isdigit()]
    if len(all_numbers_in_intro) > 4:
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.INTRODUCTION_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # Tag Validation.
    user_tag = user.profile.new_tag.first()
    tag_name = user_tag.name if user_tag else None

    all_tags = tag_services.get_all_tags()

    # Do this validation only if tag for user is present.
    if tag_name:
        for tag in all_tags:
            if tag.name == tag_name:
                continue

            # If any other tag name apart from the user's tag is
            # mentioned in the introduction. Validation for the
            # user fails.
            if re.search(tag.name, introduction, re.IGNORECASE):
                validation = models.UserValidation.objects.update_or_create(
                    user=user,
                    rule=constants.INTRODUCTION_VALIDATION,
                    defaults={
                        "result": constants.VALIDATION_SCORE_HIGH_ENUM
                    }
                )
                validation.is_validated = False

    # If the validation failed by the rules written, is_validated will be
    # False at this point.
    validation.save()

    return validation


def validate_based_on_education(user):
    """Validate a user based on his education level.

    Args:
        user(User): User we are validating based on his education.

    """
    validation = get_validation_for_user_and_rule(user, rule=constants.EDUCATION_LEVEL_VALIDATION)

    if validation:
        # If the user's validation failed and is marked as validated manually
        # don't run the validation again.
        if validation.is_validated:
            return

        # Marking the validation object as is_validated True so that if the
        # validation doesn't fail for the user. Validation is passed.
        validation.is_validated = False

    if not user.has_profile:
        return

    profile = user.profile

    if (
            profile.education_level
            and profile.education_level == user_constants.EDUCATION_LEVEL_HIGH_SCHOOL
            and profile.score <= 40
    ):
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.EDUCATION_LEVEL_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # If the validation failed by the rules written, is_validated will be
    # False at this point.
    validation.save()

    return validation


def validate_based_on_linkedin_url(user):
    """Validate a user based on linkedin url provided by the user.

    Args:
        user(User): User we are validating based on linkedin url.

    """
    validation = get_validation_for_user_and_rule(user, rule=constants.LINKEDIN_URL_VALIDATION)

    if validation:
        # If the user's validation failed and is marked as validated manually
        # don't run the validation again.
        if validation.is_validated:
            return

        # Marking the validation object as is_validated True so that if the
        # validation doesn't fail for the user. Validation is passed.
        validation.is_validated = False

    if not user.has_profile:
        return

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
        validation.is_validated = False
        validation.save()

        return validation

    if not _validate_linkedin_profile_url(linkedin_url):
        validation = models.UserValidation.objects.update_or_create(
            user=user,
            rule=constants.LINKEDIN_URL_VALIDATION,
            defaults={
                "result": constants.VALIDATION_SCORE_HIGH_ENUM
            }
        )
        validation.is_validated = False

    # If the validation failed by the rules written, is_validated will be
    # False at this point.
    validation.save()

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
