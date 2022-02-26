import datetime

from crater.creator import models
from crater.creator import signals
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import F, Count, Value, Window, Case, When
from django.db.models.functions import TruncDate, Coalesce, Concat, RowNumber


def create_default_community_for_creator(creator):
    """Create default community for a creator.

    Args:
        creator(Creator): Creator for whom we are
            creating a default community.

    """
    user = creator.user
    community_name = user.display_name + "'s Club"

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
    community_member, created = models.CommunityMember.objects.get_or_create(
        user=user,
        community=community
    )

    if created:
        signals.user_added_to_community.send(
            sender=community_member.__class__,
            community_member=community_member
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
            follower has unfollowed.

    """
    follower, created = models.Follower.objects.update_or_create(
        creator=creator,
        user=user,
        defaults={
            "unfollowed": False
        }
    )

    # Send a creator followed signal
    # when the creator is followed.
    if created:
        signals.creator_followed.send(
            sender=follower.__class__,
            follower=follower
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


def get_subscriber_count_for_creator(creator):
    """Returns count of subscribers a creator has.

    Args:
        creator(Creator): Creator on the platform.

    """
    return models.Follower.objects.filter(
        creator=creator,
        unfollowed=False,
        notify=True
    ).count()


def get_subscriber_count(user):
    """Returns count of subscribers a user has.

    Args:
        user(User): User instance of a creator

    """
    return models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False,
        notify=True
    ).count()


def get_or_create_creator(user):
    """Return a creator for the provided user

    Args:
        user(User): User model instance

    """
    creator, _ = models.Creator.objects.get_or_create(
        user=user
    )
    if not creator.certified:
        creator.certified = True
        creator.save()

    return creator


def get_follower_count(user):
    """Returns count of follower a user has.

    Args:
        user(User): User on the platform.

    """
    return models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False
    ).count()


def get_follower_count_by_month(user, followed_at):
    """Returns count of follower a user has by given month and year

    Args:
        user(User): User on the platform
        followed_at(DateTime): Followed at datetime

    """
    return models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False,
        followed_at__month=followed_at.month,
        followed_at__year=followed_at.year
    ).count()


def get_follower_growth_over_month(user, followed_at):
    """Returns follower growth percentage change over
        previous month.

    Args:
        user(User): User on the platform
        followed_at(DateTime): Followed at datetime

    """
    # Get datetime of previous month
    followed_at_prev_month = followed_at - relativedelta(months=1)

    # Get follower count for previous month
    follower_count_prev_month = get_follower_count_by_month(
        user=user,
        followed_at=followed_at_prev_month
    )

    if not follower_count_prev_month:
        return None

    # Get follower count for given month
    follower_count_given_month = get_follower_count_by_month(
        user=user,
        followed_at=followed_at
    )

    percentage_growth = round(
        (
                (follower_count_given_month - follower_count_prev_month) / follower_count_prev_month
        ) * 100,
        2
    )

    return percentage_growth


def get_follower_count_by_date(user, start_datetime, end_datetime):
    """Returns follower count by date till current date, given
        the followed_at start date.

    Args:
        user(User): User instance of creator
        start_datetime(DateTime): Followed at start datetime
        end_datetime(DateTime): Followed at end datetime

    """
    follower_count_data = models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False,
        followed_at__date__gte=start_datetime
    ).values(
        followed_at_date=TruncDate(F("followed_at__date"))
    ).annotate(
        follower_count=Count("followed_at_date")
    )

    follower_count_by_date = list(follower_count_data)

    # Followed at dates which has follower count
    present_dates = follower_count_data.values_list("followed_at_date", flat=True)

    # Add missing dates to response
    delta = end_datetime - start_datetime
    for i in range(delta.days + 1):
        date = start_datetime + datetime.timedelta(days=i)
        if date not in present_dates:
            follower_count_by_date.append({
                "followed_at_date": date,
                "follower_count": 0
            })

    # Sort by followed_at_date
    follower_count_by_date.sort(key=lambda x: x["followed_at_date"])

    return follower_count_by_date


def get_top_creators_by_month(followed_at_date, count=5, user=None):
    """Returns top creators by month and rank of requested creator.

    Args:
        followed_at_date(DateTime): Followed at datetime
        count(int): Number of top creators to be returned
        user(User): User instance of a creator

    """
    requested_creator_rank = None

    top_creators = models.Follower.objects.filter(
        followed_at__month=followed_at_date.month,
        followed_at__year=followed_at_date.year
    ).values(
        pk=F("creator__user"),
        slug=F("creator__slug"),
        name=F("creator__user__name"),
        image=F("creator__user__profile__photo")
    ).annotate(
        follower_count=Count("id", distinct=True)
    ).order_by(
        "-follower_count"
    ).annotate(
        rank=Window(expression=RowNumber())
    )

    # Return rank of requested creator
    if user:
        requested_creator_ranking_data = top_creators.filter(pk=user.pk)
        if requested_creator_ranking_data:
            requested_creator_rank = requested_creator_ranking_data.first().get("rank")

    top_creators = top_creators[:count]

    return top_creators, requested_creator_rank


def get_traffic_sources_for_creator(user):
    """Returns creator followers count by various
        traffic sources for current month.

    Args:
        user(User): User instance of a creator

    """
    traffic_source_data = models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False
    ).values(
        source_name=Case(
            When(
                user__user_source__utm_medium=user.pk,
                then=F("user__user_source__utm_source")
            ),
            default=Value("Crater")
        )
    ).annotate(
        count=Count("id", distinct=True)
    )

    return traffic_source_data


def get_percentage_creator_followers_from_crater(user):
    """Returns percentage of creator's followers from Crater.

    Args:
        user(User): User instance of a creator

    """
    # Filter creator's followers
    creator_followers = models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False
    )

    total_rsvps = creator_followers.count()

    if not total_rsvps:
        return None

    users_by_crater_count = creator_followers.exclude(
        user__user_source__utm_medium=user.pk
    ).count()

    percentage_creator_followers_from_crater = round(
        (users_by_crater_count / total_rsvps) * 100,
        2
    )

    return percentage_creator_followers_from_crater
