from django.db.models.signals import post_save
from django.dispatch import receiver

from conversations import signals as conversation_signals
from crater.creator import models, private, signals


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
    creator.subscriber_count = private.get_subscriber_count_for_creator(creator)

    # Set show_club_members to true if follower count hits 50
    if creator.follower_count >= 50 and not creator.show_club_members:
        creator.show_club_members = True
        # Marking certified True for creator's it's not marked
        # on creation.
        creator.certified = True

    creator.save()

    # If subscriber count reaches 50, send a signal.
    if creator.subscriber_count == 50:
        signals.creator_50_subscribers.send(
            sender=creator.__class__,
            creator=creator
        )

    return creator


@receiver(conversation_signals.attendee_added_to_series)
@receiver(conversation_signals.attendee_added_to_group)
def add_attendee_to_creator_followers(sender, user, group=None, series=None, *args, **kwargs):
    """Add user as a follower to the creator.

    Args:
        sender(Group/Series): Group or Series class representation.
        group(Group): Group the user joined into.
        user(User): User that joined the group.
        series(Series): Series the user joined to.

    """

    if group:
        host = group.host
    elif series:
        host = series.host
    else:
        return False

    if not host:
        return False

    creator = private.get_or_create_creator(host)
    return private.create_follower_for_creator(user, creator)


@receiver(conversation_signals.webinar_created)
def add_creator(sender, group, *args, **kwargs):
    """Add a creator object for the group host

    Args:
        sender(Group): Group class.
        group(Group): Group model instance

    """
    return private.get_or_create_creator(user=group.host)
