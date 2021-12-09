from django.db.models.signals import post_save
from django.dispatch import receiver

from conversations import signals as conversation_signals
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
    created = kwargs.get("created")
    if not created:
        return
    return private.create_default_community_for_creator(instance)


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

    # Set show_club_members to true if follower count hits 50
    if creator.follower_count >= 50 and not creator.show_club_members:
        creator.show_club_members = True

    creator.save()

    return creator


@receiver(conversation_signals.attendee_added_to_group)
def add_attendee_to_creator_followers(sender, group, user, *args, **kwargs):
    """Creates google calendar event when an attendee joins a live steam.

    Args:
        sender(Group Class): Group class representation for the group joined.
        group(Group): Group the user joined into.
        user(User): User that joined the group.

    """
    host = group.host

    try:
        creator = host.creator
    except models.Creator.DoesNotExist:
        return

    return private.create_follower_for_creator(user, creator)
