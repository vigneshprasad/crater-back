from django.utils import timezone

from users import models
from users import choices


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


def create_or_update_user_device_info(
        user,
        os,
        os_version,
        device_name,
        device_model,
        device_type
):
    """
    Create or update the User's device based on the args.

    Args:
        user(User): User whose info has to be added or updated.
        os(str): OS is the user using.
        os_version(str): Version of the OS.
        device_name(str): Device the user is using.
        device_model(str): Model number of the user's device.
        device_type(str): Type of device.

    Return:
        user_device_info(UserDeviceInfo): Device info object, created or updated.
        created(Boolean): True if the object was created else False.

    """
    user_device_info, created = models.UserDeviceInfo.objects.update_or_create(
        user=user,
        os=os,
        os_version=os_version,
        device_name=device_name,
        device_model=device_model,
        type=device_type,
        defaults={'last_used': timezone.now()}
    )
    return user_device_info, created


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
        'label': 'Education level',
        'type': 'drop-down',
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
        'label': 'Company type',
        'type': 'drop-down',
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
        'label': 'Years of experience',
        'type': 'drop-down',
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
        'label': 'Sector',
        'type': 'drop-down',
        'options': options,
        'blank': False,
    }


def get_name_field_info():
    return {
        'label': 'Name',
        'type': 'text-field',
        'options': None,
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
        'label': 'Number of employees',
        'type': 'drop-down',
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
        'label': 'Project Type',
        'type': 'drop-down',
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
        'label': 'Stage of company',
        'type': 'drop-down',
        'options': options,
        'blank': False,
    }


def get_aspiration_field_info():
    options = []
    for item in models.Profile.ASPIRATION_CHOICES:
        options.append({
            "value": item[0],
            "name": item[1],
        })
    return {
        'label': 'Aspiration',
        'type': 'drop-down',
        'options': options,
        'blank': False,
    }