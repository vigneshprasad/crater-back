# Use this file only for operations on Models.

from integrations.freshchat import models


def create_or_update_freshchat_user(user, freshchat_user_id):
    """Create or Updates a FreshChatUser for a User.

    Args:
        user(User): User on our platform.
        freshchat_user_id(str): User's id on Freshchat servers.

    Returns:
        freshchat_user(FreshChatsUser): Updated/Created FreshChatUser object.

    """

    freshchat_user = get_freshchat_user(user)

    if not freshchat_user:
        freshchat_user = models.FreshChatUser.objects.create(
            user=user,
            freshchat_user_id=freshchat_user_id
        )

    return freshchat_user


def get_freshchat_user(user):
    """Returns FreshChatUser for a User.

    Args:
        user(User): User's who's freshchat user we are fetching.

    Returns:
        FreshChatUser object or None if not found for the user.

    """
    try:
        return models.FreshChatUser.objects.get(user=user)
    except models.FreshChatUser.DoesNotExist:
        return None
