from integrations.freshchat import models


def create_or_update_freshchat_user(user, freshchat_user_id):
    """Create or Updates a FreshChatUser for a User.

    Args:
        user(User): User on our platform.
        freshchat_user_id(str): user_id of FreshChat's platform for
            the User.

    Returns:
        freshchat_user(FreshChatsUser): Updated/Created FreshChatUser object.

    """
    freshchat_user, _ = models.FreshChatUser.objects.update_or_create(
        user=user,
        freshchat_user_id=freshchat_user_id,
        defaults={}
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
