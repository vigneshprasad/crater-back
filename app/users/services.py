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
