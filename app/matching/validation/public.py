from matching.validation import constants
from matching.validation import private


def validate_user(user):
    """Validates a user's profile based on multiple factors.

    Args: User we are validating.

    """
    introduction_validation = private.validate_based_on_introduction(user)
    education_validation = private.validate_based_on_education(user)
    phone_price_validation = private.validate_based_on_phone_price(user)
    linkedin_validation = private.validate_based_on_linkedin_url(user)

    return {
        constants.PHONE_PRICE_VALIDATION: phone_price_validation.result if phone_price_validation else None,
        constants.EDUCATION_LEVEL_VALIDATION: education_validation.result if education_validation else None,
        constants.INTRODUCTION_VALIDATION: introduction_validation.result if introduction_validation else None,
        constants.LINKEDIN_URL_VALIDATION: linkedin_validation.result if linkedin_validation else None,
    }
