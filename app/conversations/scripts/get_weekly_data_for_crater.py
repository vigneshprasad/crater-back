import datetime
import warnings

from dateutil import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from conversations import constants, models
from crater.creator import models as creator_models
from integrations.dyte import models as dyte_models
from integrations.dyte.service import dyte_service
from users import constants as user_constants
from wn_analytics import models as analytics_models

DATE_JOINED_DURATION_CHOICES = [
    24,
    7 * 24,
    14 * 24,
    30 * 24
]

# Default start date in case not provided.
DEFAULT_START_DATE = datetime.datetime(2021, 1, 1)
# Start of streams (We are treating this as global start date for all metrics)
GLOBAL_START = datetime.datetime(2021, 10, 1)
# Start date to calculate Weekly active users.
GLOBAL_WAU_START = datetime.datetime(2021, 10, 4)
# Default start date for organic users calculation.
DEFAULT_ORGANIC_USERS_START_DATE = datetime.datetime(2022, 1, 17)

# Email to exclude for data.
EMAIL_TO_EXCLUDE = [
    "vignesh@worknetwork.in",
    "abhishek@worknetwork.in",
    "nishant@worknetwork.in",
    "vivan@worknetwork.in",
    "vivan@crater.club",
    "ram@worknetwork.in",
    "sujith@crater.club",
    "shivanivijay2796@gmail.com",
    "shivaniv27@yahoo.co.in",
    "rjtnndn@gmail.com",
    "sanjeevraichur29@gmail.com"
]

DEVSCRIPT_SOURCE = "Dev Script"
DEVSCRIPT_HOST_CREATOR = "+917350560609"


def _filter_group_where_host_went_live(groups):
    """Returns groups where the host went live.

    Args:
        groups(Queryset): Groups queryset we are filtering.

    """
    group_ids = []
    for group in groups:
        dmps = dyte_models.DyteMeetingParticipant.objects.filter(
            participant=group.host,
            dyte_meeting__group__host=group.host,
            last_online_at__isnull=False
        )
        # If the host didn't go online, don't add to
        # list of groups.
        if not dmps:
            continue
        group_ids.append(group.id)

    # Return a queryset from here.
    return models.Group.objects.filter(id__in=group_ids)


published_streams = models.Group.objects.filter(
    is_published=True,
    type=constants.GROUP_TYPE_WEBINAR_ENUM
)

# Only including groups where host went live.
published_streams_went_live = _filter_group_where_host_went_live(published_streams)


def get_data_for_groups_by_duration(start_date=None, end_date=None):
    """Get data for groups for duration.

    Returns:
        CSV output for per session data between start and end.

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_ORGANIC_USERS_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    groups = published_streams_went_live.filter(
        start__gte=start_datetime,
        start__lte=end_datetime
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    )

    for group in groups:

        rsvps = models.Request.objects.filter(group=group)
        req_count = 0
        organic_rsvp = 0

        for rsvp in rsvps.all():
            if rsvp.requester.email in EMAIL_TO_EXCLUDE:
                continue
            req_count += 1
            if rsvp.requester.date_joined.date() < DEFAULT_ORGANIC_USERS_START_DATE.date():
                continue
            us = analytics_models.UserSource.objects.filter(user=rsvp.requester).last()
            if not us:
                organic_rsvp += 1

        dyte_meeting = dyte_models.DyteMeeting.objects.get(group=group)
        dmps = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting=dyte_meeting,
            last_online_at__isnull=False
        ).exclude(
            participant__user_source__utm_source=DEVSCRIPT_SOURCE
        )

        host_dmp = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting=dyte_meeting,
            participant=group.host,
            last_online_at__isnull=False
        ).exclude(
            participant__username=DEVSCRIPT_HOST_CREATOR
        )
        if not len(host_dmp) == 1:
            host_end = group.start
        else:
            host_end = host_dmp[0].last_online_at

        online_count = 0
        completion = 0
        organic_online = 0
        for dmp in dmps.all():
            if dmp.participant.email in EMAIL_TO_EXCLUDE:
                continue
            if dmp.participant.email == group.host.email:
                continue
            online_count += 1
            if (host_end - dmp.last_online_at).total_seconds() > 420:
                completion += 1
            if dmp.participant.date_joined.date() < DEFAULT_ORGANIC_USERS_START_DATE.date():
                continue
            us = analytics_models.UserSource.objects.filter(
                user=dmp.participant,
            ).last()
            if not us or us.referrer:
                organic_online += 1

        categories = group.categories.all()
        categories_str = ""
        for category in categories:
            categories_str += category.name + ", "

        dyte_data = dyte_service.get_stats_for_meeting(group)
        dyte_online = len(dyte_data)
        dyte_time_spent = 0
        for d in dyte_data:
            dyte_time_spent += d["totalMinutes"]

        users_who_messaged = models.GroupMessage.objects.filter(
            group=group
        ).exclude(
            sender__email__in=EMAIL_TO_EXCLUDE
        ).values("sender").distinct().count()

        print(
            group.pk, "#",
            group.host, "#",
            group.topic, "#",
            group.start, "#",
            categories_str, "#",
            req_count, "#",
            organic_rsvp, "#",
            online_count, "#",
            completion, "#",
            organic_online, "#",
            dyte_online, "#",
            round(dyte_time_spent, 2), "#",
            users_who_messaged, "#"
        )


def run(start_date, end_date):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        all_data(start_date, end_date)


def all_data(start_date, end_date):
    # Total users.
    total_users = get_total_number_of_users(start_date=start_date, end_date=end_date)
    total_user_since_organic = get_total_users_since_organic(end_date=end_date)
    organic_users = get_organic_users_for_duration(start_date=start_date, end_date=end_date)

    # Get first RSVP.
    first_rsvp = get_number_of_rsvp_for_duration(start_date=start_date, end_date=end_date)
    # Get second RSVP.
    second_rsvp = get_number_of_rsvp_for_duration(start_date=start_date, end_date=end_date, rsvp_count=2)
    # Get third RSVP.
    third_rsvp = get_number_of_rsvp_for_duration(start_date=start_date, end_date=end_date, rsvp_count=3)

    # Get first went online.
    first_online = get_number_of_streams_watched_by_participant(start_date=start_date, end_date=end_date)
    # Get second went online.
    second_online = get_number_of_streams_watched_by_participant(
        start_date=start_date,
        end_date=end_date,
        online_count=2
    )
    # Get third went online.
    third_online = get_number_of_streams_watched_by_participant(
        start_date=start_date,
        end_date=end_date,
        online_count=3
    )

    # Get RSVP/Online after 24 hours.
    rsvp_after_24_hours = get_rsvp_after_date_joined_duration(start_date=start_date, end_date=end_date)
    # Get RSVP/Online after 7 days.
    rsvp_after_7_days = get_rsvp_after_date_joined_duration(
        start_date=start_date,
        end_date=end_date,
        duration=7 * 24
    )
    # Get RSVP/Online after 14 days.
    rsvp_after_14_days = get_rsvp_after_date_joined_duration(
        start_date=start_date,
        end_date=end_date,
        duration=14 * 24
    )
    # Get RSVP/Online after 30 days.
    rsvp_after_30_days = get_rsvp_after_date_joined_duration(
        start_date=start_date,
        end_date=end_date,
        duration=30 * 24
    )

    # Get total steamers.
    total_streamers = get_total_streamers(start_date=start_date, end_date=end_date)
    # Get organic creators.
    organic_creators = get_organic_creators(start_date=start_date, end_date=end_date)
    # Get stream performed after 24 hours.
    streams_after_24_hours = get_stream_performed_after_duration(start_date=start_date, end_date=end_date)
    # Get stream performed after 7 days.
    streams_after_7_days = get_stream_performed_after_duration(
        start_date=start_date,
        end_date=end_date,
        duration=7 * 24
    )
    # Get stream performed after 14 days.
    streams_after_14_days = get_stream_performed_after_duration(
        start_date=start_date,
        end_date=end_date,
        duration=14 * 24
    )
    # Get stream performed after 30 days.
    streams_after_30_days = get_stream_performed_after_duration(
        start_date=start_date,
        end_date=end_date,
        duration=30 * 24
    )

    # DAU for duration.
    dau = get_dau_for_duration(start_date=start_date, end_date=end_date)
    # MAU for duration.
    wau = get_wau_for_duration(start_date=start_date, end_date=end_date)
    # MAU for duration.
    mau = get_mau_for_duration(start_date=start_date, end_date=end_date)

    # Get total and average time spent on streams for participants.
    total_participant_minutes, avg_participant_minutes, _ = get_average_minutes_on_streams_participants(
        start_date=start_date,
        end_date=end_date
    )
    # Get total and average time spent on streams for speakers.
    total_streamer_minutes, avg_streamer_minutes, _ = get_average_minutes_on_streams_hosts(
        start_date=start_date,
        end_date=end_date
    )

    # Get average stream per day.
    total_streams, avg_streams_per_day = get_average_streams_per_day(start_date=start_date, end_date=end_date)

    # Get average streams streamed per month by streamers.
    avg_stream_per_month = get_average_streams_streamed_per_month(start_date=start_date, end_date=end_date)
    # Get average streams RSVP'd per month by participants.
    avg_rsvps_per_month = get_average_streams_rsvp_per_month(start_date=start_date, end_date=end_date)
    # Get average streams attended per month by participants.
    avg_stream_attended_per_month = get_average_streams_attended_per_month(start_date=start_date, end_date=end_date)

    # Get average RSVPs per stream.
    avg_stream_rsvp_per_stream = get_average_rsvps_per_stream(start_date=start_date, end_date=end_date)
    # Get average attendees per stream.
    avg_stream_attended_per_stream = get_average_attendees_per_stream(start_date=start_date, end_date=end_date)

    # Get total and average(per stream) chat messages.
    total_messages, _, avg_messages_per_stream = get_chat_messages_for_streams(
        start_date=start_date,
        end_date=end_date
    )
    users_with_chat_message = get_number_of_users_who_messaged(
        start_date=start_date,
        end_date=end_date
    )

    total_followers = get_total_followers(start_date=start_date, end_date=end_date)
    total_subscribers = get_total_subscribers(start_date=start_date, end_date=end_date)

    print("Total no. of users", total_users)
    print("Total no. of users since organic", total_user_since_organic)
    print("Organic users", organic_users)
    print("\n")

    print("First RSVP", first_rsvp)
    print("Second RSVP", second_rsvp)
    print("Third RSVP", third_rsvp)
    print("\n")

    print("Went online first", first_online)
    print("Second online", second_online)
    print("Third online", third_online)
    print("\n")

    print("RSVP after 24 hours", rsvp_after_24_hours)
    print("RSVP/Online after a week (D7)", rsvp_after_7_days)
    print("RSVP/Online after 14 days (D14)", rsvp_after_14_days)
    print("RSVP/Online after 30 days (D30)", rsvp_after_30_days)
    print("\n")

    print("DAUs (some action on platform)", dau)
    print("WAUs (some action on platform)", wau)
    print("MAUs (some action on platform)", mau)
    print("\n")

    print("Number of streamers", total_streamers)
    print("Number of organic streamers", organic_creators)
    print("Stream after 24 hours", streams_after_24_hours)
    print("Stream after a week", streams_after_7_days)
    print("Stream after 14 days", streams_after_14_days)
    print("Stream after 30 days", streams_after_30_days)
    print("\n")

    print("Time spent by users", total_participant_minutes)
    print("Time spent by streamers", total_streamer_minutes)
    print("Avg. Time Per Viewer", avg_participant_minutes)
    print("Avg. Time Per Streamer", avg_streamer_minutes)
    print("\n")

    print("Total no. of streams", total_streams)
    print("Streams per day", avg_streams_per_day)
    print("\n")

    print("Avg. sessions streamed per month (streamer)", avg_stream_per_month)
    print("Avg. sessions viewed per month (user)", avg_stream_attended_per_month)
    print("Avg. sessions RSVPed per month (user)", avg_rsvps_per_month)
    print("Avg. RSVP per Stream", avg_stream_rsvp_per_stream)
    print("Avg. Viewers per Stream", avg_stream_attended_per_stream)
    print("\n")

    print("No. of chat messages on stream", total_messages)
    print("Chat messages per stream", avg_messages_per_stream)
    print("Total users with chat message", users_with_chat_message)
    print("\n")

    print("Total Followers", total_followers)
    print("No. of Subscribers", total_subscribers)
    print("\n")


def get_streams_not_gone_live_for_duration(start_date=None, end_date=None):
    """Return count of published stream that didn't go live.

    Data Point:
        Stream not went live.

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_ORGANIC_USERS_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    published_streams_not_went_live = published_streams.difference(
        published_streams_went_live
    )
    for published_stream_not_went_live in published_streams_not_went_live:
        print(published_streams_not_went_live.id)

    return published_streams_not_went_live.count()


def get_organic_users_for_duration(start_date=None, end_date=None):
    """Return number of organic users for duration.

    Data Point:
        Organic Users

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_ORGANIC_USERS_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    start = start_datetime if \
        start_datetime > DEFAULT_ORGANIC_USERS_START_DATE.date() else DEFAULT_ORGANIC_USERS_START_DATE.date()

    data = get_user_model().objects.filter(
        date_joined__gte=start,
        date_joined__lte=end_datetime,
        groups__name=user_constants.CRATER_CLUB_GROUP,
        creator__isnull=True
    )

    return data.filter(
        Q(user_source__isnull=True) |
        Q(user_source__referrer__isnull=False)
    ).count()


def get_total_streamers(start_date=None, end_date=None):
    """Get total streamers in duration.

    Data Point:
        Number of streamers

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    start_datetime = start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date()

    hosts = published_streams_went_live.filter(
        start__gte=start_datetime,
        start__lte=end_datetime,
        host__creator__is_active=True
    ).values_list("host", flat=True)
    # Make the hosts unique.
    hosts = list(set(hosts))

    return len(hosts)


def get_total_followers(start_date=None, end_date=None):
    """Get total followers in duration.

    Data Point:
        Total Followers

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    return creator_models.Follower.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime,
        creator__is_active=True
    ).exclude(
        user__user_source__utm_source=DEVSCRIPT_SOURCE
    ).count()


def get_total_subscribers(start_date=None, end_date=None):
    """Get total subscribers in duration.

    Data Point:
        No. of Subscribers

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    return creator_models.Follower.objects.filter(
        updated_at__gte=start_datetime,
        updated_at__lte=end_datetime,
        creator__is_active=True,
        notify=True
    ).exclude(
        user__user_source__utm_source=DEVSCRIPT_SOURCE
    ).count()


def get_mau_for_duration(start_date=None, end_date=None):
    """Monthly active users.

    Data Point:
        MAU

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    # Recalculate start datetime based on GLOBAL_START.
    start_datetime = start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date()

    r = relativedelta.relativedelta(end_datetime, start_datetime)
    # Get month difference between the start and end.
    months = (r.years * 12) + r.months or 1

    all_rsvps = 0
    start = start_datetime

    for i in range(0, months):
        end = start + relativedelta.relativedelta(months=1)
        unique_rsvps = models.Request.objects.filter(
            created_at__gte=start,
            created_at__lte=end
        ).exclude(
            requester__user_source__utm_source=DEVSCRIPT_SOURCE
        ).values("requester_id").distinct()

        all_rsvps += unique_rsvps.count()
        start += relativedelta.relativedelta(months=1)

    return round(all_rsvps / months, 2)


def get_wau_for_duration(start_date=None, end_date=None):
    """Weekly active users.

    Data Points:
        WAU

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_WAU_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    # Recalculate start datetime based on GLOBAL_START.
    start_datetime = start_datetime if start_datetime > GLOBAL_WAU_START.date() else GLOBAL_WAU_START.date()

    time_spent = end_datetime - start_datetime
    days = time_spent.days
    weeks = int(days / 7)

    all_rsvps = 0
    start = start_datetime

    for i in range(0, weeks):
        end = start + timezone.timedelta(days=7)
        unique_rsvps = models.Request.objects.filter(
            created_at__gte=start,
            created_at__lte=end
        ).exclude(
            requester__user_source__utm_source=DEVSCRIPT_SOURCE
        ).values("requester_id").distinct()

        all_rsvps += unique_rsvps.count()
        start += timezone.timedelta(days=7)

    return round(all_rsvps / weeks, 2)


def get_dau_for_duration(start_date=None, end_date=None):
    """Daily active users.

    Data Point:
        DAU

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    # Recalculate start datetime based on GLOBAL_START.
    start_datetime = start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date()

    time_spent = end_datetime - start_datetime
    days = time_spent.days

    all_rsvps = 0
    start = start_datetime

    for i in range(0, days):
        end = start + timezone.timedelta(days=1)
        unique_rsvps = models.Request.objects.filter(
            created_at__gte=start,
            created_at__lte=end
        ).exclude(
            requester__user_source__utm_source=DEVSCRIPT_SOURCE
        ).values("requester_id").distinct()

        all_rsvps += unique_rsvps.count()
        start += timezone.timedelta(days=1)

    return round(all_rsvps / days, 2)


def get_organic_creators(start_date=None, end_date=None):
    """Get organic creators for duration.

    Data Point:
        Organic creators

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    # List of host that went live in the duration.
    hosts = set(list(published_streams_went_live.values_list("host", flat=True)))

    # Get creators that have gone live in the past.
    organic_creators = creator_models.Creator.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        # point_of_contact__isnull=True,
        prospector__isnull=True,
        is_active=True,
        user__in=hosts
    )

    return organic_creators.count()


def get_total_users_since_organic(start_date=None, end_date=None):
    """Get total number since organic of Crater users on the platform.

    Data Point:
        Total no. of users since organic

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_ORGANIC_USERS_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    start = start_datetime if \
        start_datetime > DEFAULT_ORGANIC_USERS_START_DATE.date() else DEFAULT_ORGANIC_USERS_START_DATE.date()

    return get_user_model().objects.filter(
        date_joined__gte=start,
        date_joined__lte=end_datetime,
        groups__name=user_constants.CRATER_CLUB_GROUP
    ).exclude(
        user_source__utm_source=DEVSCRIPT_SOURCE
    ).count()


def get_total_number_of_users(start_date=None, end_date=None):
    """Get total number of Crater users on the platform.

    Data Point:
        Total no. of users

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    return get_user_model().objects.filter(
        date_joined__gte=start_datetime,
        date_joined__lte=end_datetime,
        groups__name=user_constants.CRATER_CLUB_GROUP
    ).exclude(
        user_source__utm_source=DEVSCRIPT_SOURCE
    ).count()


def get_number_of_rsvp_for_duration(start_date=DEFAULT_START_DATE, end_date=None, rsvp_count=1):
    """Gets data for number of unique rsvps.

    Data Points:
        First RSVP.
        Second RSVP.
        Third RSVP.

    """

    if not end_date:
        end_date = timezone.now()

    unique_rsvps = models.Request.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).exclude(
        requester__user_source__utm_source=DEVSCRIPT_SOURCE
    ).values("requester_id").annotate(
        requester_count=Count("requester_id")
    ).filter(requester_count__gte=rsvp_count)

    return unique_rsvps.count()


def get_number_of_streams_watched_by_participant(start_date=None, end_date=None, online_count=1):
    """Gets number of streams joined.

     Data Points:
        Went online first
        Second online.
        Third online.

     """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    number_of_streams_joined = dyte_models.DyteMeetingParticipant.objects.filter(
        updated_at__gte=start_date,
        updated_at__lte=end_date,
        last_online_at__isnull=False
    ).exclude(
        participant__user_source__utm_source=DEVSCRIPT_SOURCE
    ).values("participant_id").annotate(
        participant_count=Count("participant_id")
    ).filter(participant_count__gte=online_count)

    return number_of_streams_joined.count()


def get_rsvp_after_date_joined_duration(start_date=None, end_date=None, duration=24):
    """Get RSVP after data joined.

    Data Points:
        RSVP after 24 hours (D1).
        RSVP/Online after a week (D7).
        RSVP/Online after 14 days (D14).
        RSVP/Online after 30 days (D30).

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    rsvp_after_date_joined_duration = []

    all_rsvps = models.Request.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).exclude(
        requester__user_source__utm_source=DEVSCRIPT_SOURCE
    ).order_by("created_at").values(
        "requester_id",
        "requester__date_joined",
        "created_at"
    )

    for rsvp in all_rsvps:
        if (rsvp["requester__date_joined"] + datetime.timedelta(hours=duration)) > rsvp["created_at"]:
            continue
        if rsvp["requester_id"] in rsvp_after_date_joined_duration:
            continue
        rsvp_after_date_joined_duration.append(rsvp["requester_id"])

    return len(rsvp_after_date_joined_duration)


def get_stream_performed_after_duration(start_date=None, end_date=None, duration=24):
    """Get stream performed by speakers after duration.

    Data points:
        Stream after 24 hours
        Stream after a week
        Stream after 14 days
        Stream after 30 days

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    number_of_streams_after_duration = []
    streams_after_duration = 0

    published_streams_went_live_within_duration = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).order_by("start")

    hosts = published_streams_went_live_within_duration.values_list("host", flat=True)
    hosts = list(set(hosts))

    for host in hosts:
        groups = published_streams_went_live_within_duration.filter(host=host)
        if groups.count() <= 1:
            continue

        first_stream = groups.first()
        last_stream = groups.last()
        if last_stream.start - first_stream.start > timezone.timedelta(hours=duration):
            streams_after_duration += 1

    return streams_after_duration


def get_average_minutes_on_streams_participants(start_date=None, end_date=None):
    """Gets total and average minutes spent on streams for participants.

    Data Point:
        Avg. Time Per Viewer.
        Time spent by users

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    groups = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    )

    total_minutes = 0
    total_participants = 0
    total_stream_time = 0

    for group in groups:
        total_time_for_stream, avg_time_for_stream, participants_joined = _get_minutes_spent_by_participants_on_stream(
            group
        )
        if not avg_time_for_stream:
            continue

        total_minutes += avg_time_for_stream
        total_stream_time += total_time_for_stream
        total_participants += participants_joined

    avg_time_spent = (total_stream_time / total_participants) if total_participants else 0
    return total_stream_time, round(avg_time_spent, 2), total_participants


def get_average_minutes_on_streams_hosts(start_date=None, end_date=None):
    """Gets total and average minutes spent on streams for hosts.

    Data Point:
        Avg. Time Per Streamer
        Time spent by streamers

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    groups = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    )

    total_minutes = 0
    total_speakers = 0
    total_stream_time = 0

    for group in groups:
        total_time_for_stream, avg_time_for_stream, speakers_joined = _get_minutes_spent_by_hosts_on_stream(group)
        if not avg_time_for_stream:
            continue

        total_minutes += avg_time_for_stream
        total_stream_time += total_time_for_stream
        total_speakers += speakers_joined

    avg_time_spent = (total_stream_time / total_speakers) if total_speakers else 0
    return total_stream_time, round(avg_time_spent, 2), total_speakers


def total_number_of_streams(start_date=None, end_date=None):
    """Total number of stream within the duration.

    Data Point:
        Total no. of streams

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_DATE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    return published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    ).count()


def get_average_streams_per_day(start_date=None, end_date=None):
    """Get streams per day.

    Data Points:
        Streams per day.

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    start = (start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date())
    time_elapsed = end_datetime - start
    days = time_elapsed.days

    streams = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    ).count()

    return streams, round(streams / days, 2)


def get_average_streams_rsvp_per_month(start_date=None, end_date=None):
    """Get average RSVP for stream per month.

    Data Point:
        Avg. sessions RSVPed per month (user)

    """

    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    all_attendees = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).values_list("attendees", flat=True)
    # Make attendees distinct.
    all_attendees = list(set(all_attendees))

    total_attendees = 0
    total_groups_attended_monthly = 0

    for attendee in all_attendees:
        try:
            user = get_user_model().objects.get(pk=attendee)
        except get_user_model().DoesNotExist:
            continue

        # Total groups attended.
        # TODO(Nishant): Should we change this to Request object calculations.
        groups = published_streams_went_live.filter(
            attendees=attendee,
            start__gte=start_date,
            start__lte=end_date
        ).exclude(
            host__username=DEVSCRIPT_HOST_CREATOR
        ).count()

        # Either october or user date joined.
        global_start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
        r = relativedelta.relativedelta(end_datetime, global_start)
        # Get month difference between the start and end.
        months_difference = (r.years * 12) + r.months

        if not groups:
            continue

        total_attendees += 1
        total_groups_attended_monthly += groups / months_difference if months_difference else groups

    return round(total_groups_attended_monthly / total_attendees, 2)


def get_average_streams_attended_per_month(start_date=None, end_date=None):
    """Gets average sessions viewed per month by participants.

    Data Point:
        Avg. sessions viewed per month (user)

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    all_attendees = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    ).values_list("attendees", flat=True)
    # Make attendees distinct.
    all_attendees = list(set(all_attendees))

    total_attendees = 0
    total_groups_attended_monthly = 0

    for attendee in all_attendees:
        try:
            user = get_user_model().objects.get(pk=attendee)
        except get_user_model().DoesNotExist:
            continue

        groups = published_streams_went_live.filter(
            attendees=attendee,
            start__gte=start_date,
            start__lte=end_date
        )
        attended_groups = 0
        for group in groups:
            dyte_meetings_attended = dyte_models.DyteMeetingParticipant.objects.filter(
                participant_id=attendee,
                dyte_meeting__group=group,
                last_online_at__isnull=False
            )
            if dyte_meetings_attended:
                attended_groups += 1

        start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
        r = relativedelta.relativedelta(end_datetime, start)
        # Get month difference between the start and end.
        months_difference = (r.years * 12) + r.months

        total_attendees += 1
        total_groups_attended_monthly += attended_groups / months_difference if months_difference else attended_groups

    return round(total_groups_attended_monthly / total_attendees, 2)


def get_average_streams_streamed_per_month(start_date, end_date=None):
    """Gets average sessions streamed per month by speakers.

    Data Point:
        Avg. sessions streamed per month (streamer)

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    all_hosts = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    ).values_list("host", flat=True)
    # Make speakers distinct.
    all_hosts = list(set(all_hosts))

    total_hosts = 0
    total_groups_streamed = 0
    total_groups_streamed_monthly = 0

    for host in all_hosts:
        try:
            user = get_user_model().objects.get(pk=host)
        except get_user_model().DoesNotExist:
            continue

        # Total groups attended.
        groups = published_streams_went_live.filter(
            host=host,
            start__gte=start_date,
            start__lte=end_date
        ).count()

        # Either october or user date joined.
        global_start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
        r = relativedelta.relativedelta(end_datetime, global_start)
        # Get month difference between the start and end.
        months_difference = (r.years * 12) + r.months

        if not groups:
            continue

        total_hosts += 1
        total_groups_streamed += groups
        total_groups_streamed_monthly += groups / months_difference if months_difference else groups

    return round(total_groups_streamed_monthly / total_hosts, 2)


def get_average_rsvps_per_stream(start_date=None, end_date=None):
    """Get average RSVPs per stream for duration.

    Data Point:
        Avg. RSVP per Stream

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    total_requests = models.Request.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM,
        group__in=published_streams_went_live
    ).exclude(
        requester__user_source__utm_source=DEVSCRIPT_SOURCE
    ).count()

    published_streams_went_live_within_duration = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__user_source__utm_source=DEVSCRIPT_SOURCE
    ).values("id").distinct().count()

    return round(total_requests / published_streams_went_live_within_duration, 2)


def get_average_attendees_per_stream(start_date=None, end_date=None):
    """Get average attendees per stream for duration.

    Data Point:
        Avg. Viewers per Stream

    """
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = GLOBAL_START
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    groups = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    ).exclude(
        host__username=DEVSCRIPT_HOST_CREATOR
    )

    total_groups = 0
    participants = []

    for group in groups:
        participant = list(
            dyte_models.DyteMeetingParticipant.objects.filter(
                dyte_meeting__group=group,
                last_online_at__isnull=False
            ).exclude(participant__in=group.speakers.all())
        )
        if not participant:
            continue
        total_groups += 1
        participants += participant

    return round(len(participants) / total_groups, 2)


def get_chat_messages_for_streams(start_date, end_date=None):
    """Return total message, average message per stream and total groups
        for duration.

    Data Points:
        No. of chat messages on stream
        Chat messages per stream

    """
    if not end_date:
        end_date = timezone.now()

    published_streams_went_live_with_duration = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date,
    )

    total_groups = 0
    total_message_count = 0

    for group in published_streams_went_live_with_duration:
        message_count = models.GroupMessage.objects.filter(
            group=group
        ).exclude(
            Q(sender__email__in=EMAIL_TO_EXCLUDE)
            | Q(sender__user_source__utm_source=DEVSCRIPT_SOURCE)
        ).count()

        if not message_count:
            continue

        total_groups += 1
        total_message_count += message_count

    return total_message_count, total_groups, round(total_message_count / total_groups, 2)


def get_number_of_users_who_messaged(start_date, end_date=None):
    """Get total number of users who sent a chat message.

    Data Points:
        Total users with chat message

    """
    if not end_date:
        end_date = timezone.now()

    published_streams_went_live_with_duration = published_streams_went_live.filter(
        start__gte=start_date,
        start__lte=end_date
    )

    return models.GroupMessage.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        group__in=published_streams_went_live_with_duration
    ).exclude(
        sender__user_source__utm_source=DEVSCRIPT_SOURCE
    ).exclude(
        sender__email__in=EMAIL_TO_EXCLUDE
    ).values("sender").distinct().count()


# -------- PRIVATE FUNCTIONS -------- #
def _get_minutes_spent_by_participants_on_stream(group):
    speakers = group.speakers.values_list("pk", flat=True)
    participants = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group_id=group.id
    ).exclude(participant_id__in=speakers)

    total_minutes = 0
    participants_joined = 0

    for participant in participants:
        # If the participant never joined the call, return.
        if not participant.last_online_at:
            continue

        # If the participant joined the call before call start.
        if participant.last_online_at < group.start:
            continue

        # Get total time spent on the call.
        time_spent = participant.last_online_at - group.start
        minutes = time_spent.seconds // 60 % 60

        # If the time spent in 0 minutes, return.
        if not minutes and minutes > 300:
            continue

        participants_joined += 1
        total_minutes += minutes

    avg_time_spent = (total_minutes / participants_joined) if participants_joined else 0
    return total_minutes, round(avg_time_spent, 2), participants_joined


def _get_minutes_spent_by_hosts_on_stream(group):
    hosts = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group_id=group.id,
        participant_id=group.host.pk
    )

    total_minutes = 0
    hosts_joined = 0

    for host in hosts:
        # If the speaker never joined the call, return.
        if not host.last_online_at:
            continue

        # If the speaker joined the call before call start.
        if host.last_online_at < group.start:
            continue

        # Get total time spent on the call.
        time_spent = host.last_online_at - group.start
        minutes = time_spent.seconds // 60 % 60

        # If the time spent in 0 minutes, return.
        if not minutes and minutes > 300:
            continue

        hosts_joined += 1
        total_minutes += minutes

    avg_time_spent = (total_minutes / hosts_joined) if hosts_joined else 0
    return total_minutes, round(avg_time_spent, 2), hosts_joined
