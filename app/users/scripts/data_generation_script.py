import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q

from users import models
from resources.meetings import models as meeting_models
from conversations import models as conversation_models


ORGANIC_BASE_SOURCE_ID = models.BaseSource.objects.get(name="Organic").id
GOOGLE_BASE_SOURCE_ID = models.BaseSource.objects.get(name="Google").id
FACEBOOK_BASE_SOURCE_ID = models.BaseSource.objects.get(name="Facebook").id


def get_all_month_by_month_data(start):
    """Print month by month data for given start and end date.

    Args:
        start(datetime.datetime): Datetime object from where we are starting
            to calculate monthly metrics.

    """
    while start < datetime.datetime.now():
        next_month_start = start + relativedelta(months=+1)
        end = next_month_start - datetime.timedelta(days=1)

        print("Acquisition Details", "*"*30)
        print("Organic User Count: ", get_organic_users_count_as_of_date(start=start, end=end))
        print("Paid User Count: ", get_paid_users_count_as_of_date(start=start, end=end))

        print("Profile Data", "*"*30)
        print("Tag Distribution of Users: ", get_users_distribution_based_on_tag_as_of_date(start=start, end=end))
        print("Experience Distribution of Users: ", get_users_distribution_based_on_experience_as_of_date(start=start, end=end))
        print("Sector Distribution of Users: ", get_users_distribution_based_on_sector_as_of_date(start=start, end=end))

        print("Conversations Metrics", "*"*30)
        print("Total Users Signed up for Conversations: ", get_total_users_signed_up_for_meetings_as_of_date(start=start, end=end))
        print("Unique Users for 1:1 Meetings: ", get_unique_users_in_meetings_as_of_date(start=start, end=end))
        print("Unique Users for Group Meetings: ", get_unique_users_in_group_meetings_as_of_date(start=start, end=end))

        print("Retention Metrics", "*"*30)
        print("Retention As of Date: ", get_retention_of_users_as_of_date(end=end))
        print("Retention Month on Month: ", get_retention_of_users_as_of_date(end=end))
        start = next_month_start


def get_organic_users_count_as_of_date(start=None, end=None):
    """Returns users with organic source."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    return models.User.objects.filter(
        ~Q(new_source__base_source__in=[GOOGLE_BASE_SOURCE_ID, FACEBOOK_BASE_SOURCE_ID]),
        date_joined__lte=end,
    ).count()


def get_paid_users_count_as_of_date(start=None, end=None):
    """Returns users with paid sources."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    return models.User.objects.filter(
        new_source__base_source__in=[GOOGLE_BASE_SOURCE_ID, FACEBOOK_BASE_SOURCE_ID],
        date_joined__lte=end,
    ).count()


def get_users_distribution_based_on_tag_as_of_date(start=None, end=None):
    """Get user distribution based on tag as of the given date."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    tag_to_user_count = {}
    user_queryset = models.User.objects.filter(date_joined__lte=end)

    for user in user_queryset:
        if not user.has_profile:
            continue

        profile = user.profile
        tag_name = profile.new_tag.first().name if profile.new_tag.first() else None
        if not tag_name:
            continue

        if not tag_to_user_count.get(tag_name):
            tag_to_user_count[tag_name] = 1
            continue

        tag_to_user_count[tag_name] += 1

    return tag_to_user_count


def get_users_distribution_based_on_experience_as_of_date(start=None, end=None):
    """Get user distribution based on experience as of the given date."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    experience_to_user_count = {}

    user_queryset = models.User.objects.filter(date_joined__lte=end)
    for user in user_queryset:

        if not user.has_profile:
            continue

        profile = user.profile
        experience = profile.years_of_experience
        if not experience:
            continue

        experience_str = dict(models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[experience] if experience else None
        if not experience_str:
            continue

        if not experience_to_user_count.get(experience_str):
            experience_to_user_count[experience_str] = 1
            continue

        experience_to_user_count[experience_str] += 1

    return experience_to_user_count


def get_users_distribution_based_on_sector_as_of_date(start=None, end=None):
    """Get user distribution based on sector as of the given date."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    sector_to_user_count = {}

    user_queryset = models.User.objects.filter(date_joined__lte=end)

    for user in user_queryset:

        if not user.has_profile:
            continue

        profile = user.profile
        sector = profile.sector
        if not sector:
            continue

        sector_str = dict(models.Profile.SECTOR_CHOICES)[sector] if sector else None
        if not sector_str:
            continue

        if not sector_to_user_count.get(sector_str):
            sector_to_user_count[sector_str] = 1
            continue

        sector_to_user_count[sector_str] += 1

    return sector_to_user_count


def get_total_users_signed_up_for_meetings_as_of_date(start=None, end=None):
    """Get all users that have signed up for a meeting."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    return meeting_models.MeetingPreference.objects.filter(
        created_at__lte=end
    ).count()


def get_unique_users_in_meetings_as_of_date(start=None, end=None):
    """Get unique users who did 1:1 meetings."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    unique_participants = set()

    meetings = meeting_models.Meeting.objects.filter(end__lte=end)
    for meeting in meetings:
        unique_participants.update([str(participant.pk) for participant in meeting.participants.all()])

    return len(unique_participants)


def get_number_of_meetings_as_of_date(start=None, end=None):
    """Get number of 1:1 meetings done."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    meetings = meeting_models.Meeting.objects.filter(end__lte=end)
    return meetings.count()


def get_unique_users_in_group_meetings_as_of_date(start=None, end=None):
    """Get unique users who did groups meetings."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()
    unique_speakers = set()
    group_meetings = conversation_models.Group.objects.filter(end__lte=end)
    for group_meeting in group_meetings:
        unique_speakers.update([str(speaker.pk) for speaker in group_meeting.speakers.all()])
    return len(unique_speakers)


def get_number_of_group_meetings_as_of_date(start=None, end=None):
    """Get number of group meetings done."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()
    group_meetings = conversation_models.Group.objects.filter(end__lte=end)
    return group_meetings.count()


def get_retention_of_users_as_of_date(start=None, end=None):
    """Get retention numbers before a date."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()

    one = 0
    two = 0
    three = 0
    four = 0
    five = 0
    six = 0
    seven = 0
    eight = 0
    nine = 0
    ten = 0
    fifteen = 0
    twenty = 0

    user_queryset = models.User.objects.all()

    for user in user_queryset:

        meetings = meeting_models.Meeting.objects.filter(
            participants=user,
            created_at__lte=end
        )
        group_meetings = conversation_models.Group.objects.filter(
            speakers=user,
            created_at__lte=end
        )

        total_conversations_count = meetings.count() + group_meetings.count()

        if total_conversations_count > 0:
            one += 1
        if total_conversations_count > 1:
            two += 1
        if total_conversations_count > 2:
            three += 1
        if total_conversations_count > 3:
            four += 1
        if total_conversations_count > 4:
            five += 1
        if total_conversations_count > 5:
            six += 1
        if total_conversations_count > 6:
            seven += 1
        if total_conversations_count > 7:
            eight += 1
        if total_conversations_count > 8:
            nine += 1
        if total_conversations_count > 9:
            ten += 1
        if total_conversations_count > 14:
            fifteen += 1
        if total_conversations_count > 19:
            twenty += 1

    print("1+ conversations: ", one)
    print("2+ conversations: ", two)
    print("3+ conversations: ", three)
    print("4+ conversations: ", four)
    print("5+ conversations: ", five)
    print("6+  conversations: ", six)
    print("7+ conversations: ", seven)
    print("8+ conversations: ", eight)
    print("9+ conversations: ", nine)
    print("10+ conversations: ", ten)
    print("15+ conversations: ", fifteen)
    print("20+ conversations: ", twenty)


def get_retention_of_users_monthly(start=None, end=None):
    """Get retention metric month on month."""
    start = start if start else datetime.datetime(2020, 1, 1)
    end = end if end else datetime.datetime.now()
    one = 0
    two = 0
    three = 0
    four = 0
    five = 0
    six = 0
    seven = 0
    eight = 0
    nine = 0
    ten = 0
    fifteen = 0
    twenty = 0

    user_queryset = models.User.objects.all()

    for user in user_queryset:

        meetings = meeting_models.Meeting.objects.filter(
            participants=user,
            created_at__gte=start,
            created_at__lte=end
        )
        group_meetings = conversation_models.Group.objects.filter(
            speakers=user,
            created_at__gte=start,
            created_at__lte=end
        )

        total_conversations_count = meetings.count() + group_meetings.count()

        if total_conversations_count > 0:
            one += 1
        if total_conversations_count > 1:
            two += 1
        if total_conversations_count > 2:
            three += 1
        if total_conversations_count > 3:
            four += 1
        if total_conversations_count > 4:
            five += 1
        if total_conversations_count > 5:
            six += 1
        if total_conversations_count > 6:
            seven += 1
        if total_conversations_count > 7:
            eight += 1
        if total_conversations_count > 8:
            nine += 1
        if total_conversations_count > 9:
            ten += 1
        if total_conversations_count > 14:
            fifteen += 1
        if total_conversations_count > 19:
            twenty += 1

    print("1+ conversations: ", one)
    print("2+ conversations: ", two)
    print("3+ conversations: ", three)
    print("4+ conversations: ", four)
    print("5+ conversations: ", five)
    print("6+  conversations: ", six)
    print("7+ conversations: ", seven)
    print("8+ conversations: ", eight)
    print("9+ conversations: ", nine)
    print("10+ conversations: ", ten)
    print("15+ conversations: ", fifteen)
    print("20+ conversations: ", twenty)
