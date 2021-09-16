from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.creator import models
from crater.creator import private
from crater.creator import signals


@receiver(post_save, sender=models.Creator)
def create_default_community_for_creator(sender, instance, *args, **kwargs):
    """Creates default community for a creator.

    Note:
        Creates a community on post_save of a creator, at
            the time of creation.

    """
    created = kwargs["created"]
    if not created:
        return
    private.create_default_community_for_creator(instance)


@receiver(signals.creator_followed)
def add_follower_to_creator_community(sender, follower, *args, **kwargs):
    """Add new follower to creator's default community.

    Args:
        sender(class): Follower class.
        follower(Follower): Follower object.

    """
    creator = follower.creator
    community = private.get_default_community_for_creator(creator)
    return private.add_user_to_community(follower.user, community)


@receiver(signals.creator_unfollowed)
@receiver(signals.creator_followed)
def update_follower_count(sender, follower, *args, **kwargs):
    """Update follower count on creator for every follow and unfollow that happens.

    Args:
        sender(class): Follower class.
        follower(Follower): Follower object.

    """
    creator = follower.creator
    creator.follower_count = private.get_follower_count_for_creator(creator)
    creator.save()
