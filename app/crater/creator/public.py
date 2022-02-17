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


def get_subscribed_creators(user):
    """Return creators users has subscribed to (notify).

    Args:
        user(User): User we are getting subscribed creator for.

    """
    follow_objs = user.following.filter(notify=True)
    return [follow_obj.creator for follow_obj in follow_objs]
