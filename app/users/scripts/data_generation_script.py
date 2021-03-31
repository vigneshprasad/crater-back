import datetime
from dateutil.relativedelta import relativedelta

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
        print("Organic User Count: ", get_organic_users_count(start=start, end=end))
        print("Paid User Count: ", get_paid_users_count(start=start, end=end))

        print("Profile Data", "*"*30)
        print("Tag Distribution of Users: ", get_users_distribution_based_on_tag(start=start, end=end))
        print("Experience Distribution of Users: ", get_users_distribution_based_on_experience(start=start, end=end))
        print("Sector Distribution of Users: ", get_users_distribution_based_on_sector(start=start, end=end))

        print("Conversations Metrics: ", "*"*30)
        print("Total Users Signed up for Conversations: ", get_total_users_signed_up_for_meetings(start=start, end=end))
        print("Unique Users for 1:1 Meetings: ", get_unique_participants_in_meetings(start=start, end=end))
        print("Unique Users for Group Meetings: ", get_unique_participants_in_group_meetings(start=start, end=end))

        print("Meetings Count: ", get_retention_of_users(start=start, end=end))
        start = next_month_start


def get_organic_users_count(start=None, end=None):
    """Returns users with organic source."""
    if not (start and end):
        return models.User.objects.filter(
            new_source__base_source=ORGANIC_BASE_SOURCE_ID
        ).count()

    return models.User.objects.filter(
        new_source__base_source=ORGANIC_BASE_SOURCE_ID,
        date_joined__gte=start,
        date_joined__lte=end,
    ).count()


def get_paid_users_count(start=None, end=None):
    """Returns users with paid sources."""
    if not (start and end):
        return models.User.objects.filter(
            new_source__base_source__in=[GOOGLE_BASE_SOURCE_ID, FACEBOOK_BASE_SOURCE_ID]
        ).count()

    return models.User.objects.filter(
        new_source__base_source__in=[GOOGLE_BASE_SOURCE_ID, FACEBOOK_BASE_SOURCE_ID],
        date_joined__gte=start,
        date_joined__lte=end,
    ).count()


def get_users_distribution_based_on_tag(start=None, end=None):
    tag_to_user_count = {}

    user_queryset = models.User.objects.filter(date_joined__gte=start, date_joined__lte=end) if (
            start and end) else models.User.objects.all()

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


def get_users_distribution_based_on_experience(start=None, end=None):
    experience_to_user_count = {}

    user_queryset = models.User.objects.filter(date_joined__gte=start, date_joined__lte=end) if (
                start and end) else models.User.objects.all()

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


def get_users_distribution_based_on_sector(start=None, end=None):
    sector_to_user_count = {}

    user_queryset = models.User.objects.filter(date_joined__gte=start, date_joined__lte=end) if (
                start and end) else models.User.objects.all()

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


def get_total_users_signed_up_for_meetings(start=None, end=None):
    if not (start and end):
        return meeting_models.MeetingPreference.objects.all().count()

    return meeting_models.MeetingPreference.objects.filter(
        created_at__gte=start,
        created_at__lte=end
    ).count()


def get_unique_participants_in_meetings(start=None, end=None):
    unique_participants = set()

    if start and end:
        meetings = meeting_models.Meeting.objects.filter(start__gte=start, end__lte=end)
    else:
        meetings = meeting_models.Meeting.objects.all()

    for meeting in meetings:
        unique_participants.update([str(participant.pk) for participant in meeting.participants.all()])

    return len(unique_participants)


def get_number_of_meetings(start=None, end=None):
    if not (start and end):
        meetings = meeting_models.Meeting.objects.all()
        return meetings.count()

    meetings = meeting_models.Meeting.objects.filter(start__gte=start, end__lte=end)
    return meetings.count()


def get_unique_participants_in_group_meetings(start=None, end=None):
    unique_speakers = set()
    if start and end:
        group_meetings = conversation_models.Group.objects.filter(start__gte=start, end__lte=end)
    else:
        group_meetings = conversation_models.Group.objects.all()

    for group_meeting in group_meetings:
        unique_speakers.update([str(speaker.pk) for speaker in group_meeting.speakers.all()])

    return len(unique_speakers)


def get_number_of_group_meetings(start=None, end=None):
    if not (start and end):
        group_meetings = conversation_models.Group.objects.all()
        return group_meetings.count()

    group_meetings = conversation_models.Group.objects.filter(start__gte=start, end__lte=end)
    return group_meetings.count()


def get_retention_of_users(end=None):
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
