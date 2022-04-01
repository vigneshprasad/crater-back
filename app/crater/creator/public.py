from django.contrib.auth import get_user_model

from crater.creator import models
from crater.creator import signals


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


def get_or_create_follower_for_user(attendee_id, creator_id):
    """Gets of creates a follower for a creator.

        Args:
            attendee_id(uuid): PK of the user who is the follower.
            creator_id(int): ID of the creator being followed by the
                user.

        Note:
            Updates the follower to unfollowed=False if the
                follower has unfollowed.

        """
    follower, created = models.Follower.objects.get_or_create(
        creator_id=creator_id,
        user_id=attendee_id
    )

    # Send a creator followed signal
    # when the creator is followed.
    if created:
        signals.creator_followed.send(
            sender=follower.__class__,
            follower=follower
        )

    return follower
