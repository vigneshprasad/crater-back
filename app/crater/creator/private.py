import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import F, Count, Value, Window, Case, When, Q, DateField
from django.db.models.functions import DenseRank, TruncMonth

from crater.creator import models
from crater.creator import signals


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


def get_top_creators_by_date_range(start_date, end_date, count=5, user=None):
    """Returns top creators by date range and rank of requested creator.

    Args:
        start_date(DateTime): Start date
        end_date(DateTime): End date
        count(int): Number of top creators to be returned
        user(User): User instance of a creator

    """
    requested_creator_rank = None

    rank_by_follower_count = Window(
        expression=DenseRank(),
        order_by=F("follower_count").desc()
    )

    top_creators = models.Follower.objects.filter(
        creator__certified=True,
        followed_at__date__range=[start_date, end_date]
    ).values(
        pk=F("creator__user"),
        slug=F("creator__slug"),
        name=F("creator__user__name"),
        image=F("creator__user__profile__photo")
    ).annotate(
        follower_count=Count("id", distinct=True)
    ).annotate(
        rank=rank_by_follower_count
    )

    # Return rank of requested creator
    if user:
        for creator in top_creators:
            if creator.get("pk") == user.pk:
                requested_creator_rank = creator.get("rank")
                break

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
                user__user_source__referrer__pk=user.pk,
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
    # Filter creator's RSVPs
    creator_followers = models.Follower.objects.filter(
        creator__user=user,
        unfollowed=False
    )

    total_followers = creator_followers.count()

    if not total_followers:
        return None

    users_by_crater_count = creator_followers.exclude(
        user__user_source__referrer__pk=user.pk
    ).count()

    percentage_creator_followers_from_crater = round(
        (users_by_crater_count / total_followers) * 100,
        2
    )

    return percentage_creator_followers_from_crater


def get_creator_stream_stats(user):
    """Returns count for total streams, upcoming streams
     and past streams

    Args:
         user(User): User instance of a creator

    """
    now = datetime.datetime.now()

    stats = list(models.Creator.objects.filter(
        is_active=True,
        user=user
    ).annotate(
        total_streams=Count("user__groups_hosted"),
        total_upcoming_streams=Count(
            "user__groups_hosted",
            Q(
                user__groups_hosted__is_published=True,
                user__groups_hosted__is_live=False,
                user__groups_hosted__closed=False,
                user__groups_hosted__start__gte=now
            )
        ),
        total_past_streams=Count(
            "user__groups_hosted",
            Q(
                user__groups_hosted__is_published=True,
                user__groups_hosted__is_live=False,
                user__groups_hosted__closed=True,
                user__groups_hosted__start__lt=now
            )
        )
    ).values(
        "total_streams",
        "total_upcoming_streams",
        "total_past_streams"
    ))

    if stats:
        stats = stats[0]
    else:
        stats = {}

    return stats


def get_total_creators():
    """Return total number of active creators."""

    return models.Creator.objects.filter(
        is_active=True
    ).count()


def get_follower_count_by_month_and_year(user, start, end):
    """Return creator follower count by month and year.

    Args:
        user(User): User instance of creator
        start(DateTime): Start datetime
        end(DateTime): End datetime

    """
    follower_count_data = models.Follower.objects.filter(
        unfollowed=False,
        notify=True,
        creator__user=user,
        followed_at__date__gte=start
    ).values(
        key=TruncMonth(
            F("followed_at"),
            output_field=DateField()
        )
    ).annotate(
        value=Count("key")
    )

    follower_count_by_month_and_year = list(follower_count_data)

    # Followed at dates which has follower count
    present_dates = follower_count_data.values_list("key", flat=True)

    delta = (end.year - start.year) * 12 + (end.month - start.month)

    for i in range(1, delta + 1):
        date = (start + relativedelta(months=i)).date()
        if date not in present_dates:
            follower_count_by_month_and_year.append({
                "key": date,
                "value": 0
            })

    # Sort by rsvp_at date
    follower_count_by_month_and_year.sort(key=lambda x: x["key"])

    # Format rsvp_at date
    [x.update({"key": x["key"].strftime("%b %Y")}) for x in follower_count_by_month_and_year]

    return follower_count_by_month_and_year
