import datetime
from itertools import chain

from django.db.models import Count, ExpressionWrapper, F, Sum, Q
from django.db.models.fields import DurationField
from django.db.models.functions import Coalesce

from users import models
from users import constants
from tags import models as tag_models
from conversations import models as conversation_models
from conversations import private as conversation_private

from resources.meetings import models as meeting_models


def get_admin_user():
    return models.User.objects.get(email=constants.ADMIN_USER_EMAIL)


def get_users_for_ids(user_ids):
    """
    Returns user objects for given list of user_ids.

    Args:
        user_ids(list): List of user ids.

    Returns:
        List of user objects for the provided ID"s

    """
    return list(models.User.objects.filter(
        pk__in=user_ids
    ))


def get_social_account_info(social_account):
    data = {}
    if not social_account:
        return data
    extra_data = social_account.extra_data
    if social_account.provider == "google":
        data = {
            "photo_url": extra_data["picture"]
        }
    return data


def get_education_level_field_info():
    options = []
    for item in models.Profile.EDUCATION_LEVEL_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_EDUCATION_LEVEL_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_company_type_field_info():
    options = []
    for item in models.Profile.COMPANY_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_COMPANY_TYPE_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_company_type_advised_field_info():
    options = []
    for item in models.Profile.COMPANY_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_COMPANY_TYPE_ADVISED_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_years_of_experience_field_info():
    options = []
    for item in models.Profile.YEARS_OF_EXPERIENCE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_YEARS_OF_EXP_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_sector_field_info():
    options = []
    for item in models.Profile.SECTOR_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_SECTOR_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_company_name_field_info():
    return {
        "label": constants.PROFILE_COMPANY_NAME_LABEL,
        "type": constants.PROFILE_FIELD_TEXT_TYPE,
        "options": None,
        "blank": False,
    }


def get_other_tag_field_info():
    return {
        "label": constants.PROFILE_OTHER_TAG_LABEL,
        "type": constants.PROFILE_FIELD_TEXT_TYPE,
        "options": None,
        "blank": False,
    }


def get_name_field_info():
    return {
        "label": constants.PROFILE_NAME_LABEL,
        "type": constants.PROFILE_FIELD_TEXT_TYPE,
        "options": None,
        "blank": False,
    }


def get_companies_invested_field_info():
    options = []
    for item in models.Profile.COMPANIES_INVESTED_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_COMPANIES_INVESTED_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_number_of_employees_field_info():
    options = []
    for item in models.Profile.NUMBER_OF_EMPLOYEE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_NUMBER_OF_EMPLOYEES_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_project_type_field_info():
    options = []
    for item in models.Profile.PROJECT_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_PROJECT_TYPE_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_stage_of_company_field_info():
    options = []
    for item in models.Profile.STAGE_OF_COMPANY_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        "label": constants.PROFILE_STAGE_OF_COMPANY_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_aspiration_field_info():
    tags = tag_models.Tag.objects.filter(is_active=True)
    options = []
    for tag in tags:
        options.append({
            "value": tag.id,
            "name": tag.name,
        })
    return {
        "label": constants.PROFILE_ASPIRATION_LABEL,
        "type": constants.PROFILE_FIELD_DROPDOWN_TYPE,
        "options": options,
        "blank": False,
    }


def get_user_with_number_of_meetings(number_of_meeting):
    """Return all users with some minimum number of meetings
        on the platform.

    Args:
        number_of_meeting(int): Minimum number of meetings
            a user should have to be in this list.

    Returns:
        Return list of user_pks not user objects for all
            users with minimum number of meetings.

    """
    return meeting_models.Meeting.objects.all().values("participants").annotate(
        number_of_meetings=Count("participants")
    ).filter(
        number_of_meetings__gte=number_of_meeting
    ).values_list("participants", flat=True)


def create_user_referral(new_user, referrer):
    """Create user referral.

    Args:
        new_user(User): Referred user
        referrer(User): User who has referred

    """
    if referrer and referrer.is_creator:
        return

    return models.UserReferral.objects.create(
        user=new_user,
        referrer=referrer
    )


def get_referrals_summary(user_referrals):
    """Return referrals summary information.

    Args:
        user_referrals(list(UserReferrals)): UserReferrals model queryset.

    """
    referrals_summary = user_referrals.aggregate(
        total_referrals=Count("id"),
        total_payable=Sum("amount"),
        paid_out=Coalesce(Sum(
            "amount",
            filter=Q(status=constants.REFERRAL_STATUS_PAID_ENUM)
        ), 0),
        outstanding_payment=Sum("amount") - Coalesce(Sum(
            "amount",
            filter=Q(status=constants.REFERRAL_STATUS_PAID_ENUM)
        ), 0)
    )

    return referrals_summary


def get_user_category(user, category):
    """Return user category.

    Args:
        user(User): user who wants to follow/unfollow a category.
        category(Category): category to be followed/unfollowed.

    """

    try:
        user_category = models.UserCategory.objects.get(
            user=user,
            category=category,
            followed=True
        )
    except models.UserCategory.DoesNotExist:
        return None

    return user_category


def user_category_followed(user, category):
    """Returns user category followed status.

    Args:
        user(User): User who has followed the category
        category(Category): Category followed by user

    """

    user_category = get_user_category(
        user=user,
        category=category
    )

    if not user_category:
        return False

    return True


def update_or_create_user_category(user, category, follow):
    """Update or create user category object.

    Args:
        user(User): User who wants to follow/unfollow
        category(Category): Category to be followed/unfollowed
        follow(boolean): follow/unfollow status

    """
    defaults = {"followed": follow}
    now = datetime.datetime.now()

    if follow:
        defaults["followed_at"] = now
    else:
        defaults["unfollowed_at"] = now

    user_category, _ = models.UserCategory.objects.update_or_create(
        user=user,
        category=category,
        defaults=defaults
    )

    return user_category
