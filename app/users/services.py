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

