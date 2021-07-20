from django.db.models import Count

from users import models
from users import choices
from tags import models as tag_models

from resources.meetings import models as meeting_models


def get_admin_user():
    return models.User.objects.get(email=choices.ADMIN_USER_EMAIL)


def get_users_for_ids(user_ids):
    """
    Returns user objects for given list of user_ids.

    Args:
        user_ids(list): List of user ids.

    Returns:
        List of user objects for the provided ID's

    """
    return list(models.User.objects.filter(
        pk__in=user_ids
    ))


def get_social_account_info(social_account):
    data = {}
    if not social_account:
        return data
    extra_data = social_account.extra_data
    if social_account.provider == 'google':
        data = {
            'photo_url': extra_data['picture']
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
        'label': choices.PROFILE_EDUCATION_LEVEL_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_company_type_field_info():
    options = []
    for item in models.Profile.COMPANY_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_COMPANY_TYPE_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_company_type_advised_field_info():
    options = []
    for item in models.Profile.COMPANY_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_COMPANY_TYPE_ADVISED_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_years_of_experience_field_info():
    options = []
    for item in models.Profile.YEARS_OF_EXPERIENCE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_YEARS_OF_EXP_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_sector_field_info():
    options = []
    for item in models.Profile.SECTOR_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_SECTOR_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_company_name_field_info():
    return {
        "label": choices.PROFILE_COMPANY_NAME_LABEL,
        "type": choices.PROFILE_FIELD_TEXT_TYPE,
        "options": None,
        "blank": False,
    }


def get_other_tag_field_info():
    return {
        "label": choices.PROFILE_OTHER_TAG_LABEL,
        "type": choices.PROFILE_FIELD_TEXT_TYPE,
        "options": None,
        "blank": False,
    }


def get_name_field_info():
    return {
        'label': choices.PROFILE_NAME_LABEL,
        'type': choices.PROFILE_FIELD_TEXT_TYPE,
        'options': None,
        'blank': False,
    }


def get_companies_invested_field_info():
    options = []
    for item in models.Profile.COMPANIES_INVESTED_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_COMPANIES_INVESTED_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_number_of_employees_field_info():
    options = []
    for item in models.Profile.NUMBER_OF_EMPLOYEE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_NUMBER_OF_EMPLOYEES_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_project_type_field_info():
    options = []
    for item in models.Profile.PROJECT_TYPE_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_PROJECT_TYPE_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_stage_of_company_field_info():
    options = []
    for item in models.Profile.STAGE_OF_COMPANY_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': choices.PROFILE_STAGE_OF_COMPANY_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
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
        'label': choices.PROFILE_ASPIRATION_LABEL,
        'type': choices.PROFILE_FIELD_DROPDOWN_TYPE,
        'options': options,
        'blank': False,
    }


def get_all_user_more_than_3_meetings():
    return meeting_models.Meeting.objects.all().values("participants").annotate(
        num_meetings=Count('participants')
    ).filter(num_meetings__gt=2).values_list("participants", flat=True)
