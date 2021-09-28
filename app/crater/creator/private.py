from crater.creator import models


def create_default_community_for_creator(creator):
    """Create default community for a creator.

    Args:
        creator(Creator): Creator for whom we are
            creating a default community.

    """
    user = creator.user
    community_name = user.name.title() + "'s Club"

    community = models.Community.objects.create(
        name=community_name,
        creator=creator,
        is_default=True
    )

    return community


def get_default_community_for_creator(creator):
    """Returns default community for a creator.

    Args:
        creator(Creator): Creator object or creator object id
            for whom we are getting the default community.

    """
    return models.Community.objects.filter(
        creator=creator,
        is_default=True,
        is_active=True
    ).first()


def get_member_for_user_and_community_id(user, community_id):
    """Return community member object for a user
        and community.

    Args:
        user(User): User for whom we are looking for
            community member object.
        community_id(integer): Id of the Community for which
            we are getting the community member for.

    """
    return models.CommunityMember.objects.filter(
        user=user,
        community_id=community_id
    ).first()


def add_user_to_community(user, community):
    """Adds a user to community.

    Args:
        user(User): User being added to the community.
        community(Community): Community the user is being
        added to.

    """
    community_member, _ = models.CommunityMember.objects.get_or_create(
        user=user,
        community=community
    )

    return community_member


def get_follower_for_user_and_creator_id(user, creator_id):
    """Returns follower object for user and creator.

    Args:
        user(User): User who is the follower.
        creator_id(integer): ID of Creator being followed by the
            user.

    """
    try:
        follower = models.Follower.objects.get(
            creator_id=creator_id,
            user=user
        )
    except models.Follower.DoesNotExist:
        return None

    return follower


def create_follower_for_creator(user, creator):
    """Creates a follower for a creator.

    Args:
        user(User): User who is the follower.
        creator(Creator): Creator being followed by the
            user.

    Note:
        Updates the follower to unfollowed=False if the
            the follower has unfollowed.

    """
    follower, created = models.Follower.objects.update_or_create(
        creator=creator,
        user=user,
        defaults={
            "unfollowed": False
        }
    )

    return follower


def get_follower_count_for_creator(creator):
    """Returns count of follower a creator has.

    Args:
        creator(Creator): Creator on the platform.

    """
    return models.Follower.objects.filter(
        creator=creator,
        unfollowed=False
    ).count()
