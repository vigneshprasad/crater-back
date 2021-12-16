from crater.creator import models


def get_creator_for_user(user):
    """Returns a creator object for user if
        one exists.

    """
    if not user:
        return None

    try:
        return user.creator
    except models.Creator.DoesNotExist:
        return None
