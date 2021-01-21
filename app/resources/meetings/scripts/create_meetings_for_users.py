import csv
import datetime
from urllib import request as urllib_request

from resources.meetings import choices
from resources.meetings import services
from users import models as user_models


FIELDS = [
    "Email A",
    "Email B",
    "Meeting Time (%d/%m%/%y %H:%M)"
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_data.csv",
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    config = services.get_current_week_meeting_config()

    if not config:
        print("No Active Config.")
        return

    print("Config: ", config.pk)

    for row in reader:
        print("Start", "-" * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email_a = row.get("Email A").strip()
        email_b = row.get("Email B").strip()
        meeting_time = row.get("Meeting Time").strip()

        # Getting the users if present.
        user_a, user_b = None, None

        try:
            user_a = user_models.User.objects.get(email=email_a)
            print("User {}".format(email_a))
        except user_models.User.DoesNotExist:
            print("*" * 5, "User Does Not Exist - {}".format(email_a))

        try:
            user_b = user_models.User.objects.get(email=email_b)
            print("User {}".format(email_b))
        except user_models.User.DoesNotExist:
            print("*" * 5, "User Does Not Exist - {}".format(email_b))

        # Check if users have met before.
        common_meetings = _check_if_users_had_a_meeting(user_a, user_b)
        if common_meetings:
            print("*" * 5, "Users met before. Meeting ID: {}".format(common_meetings))
            continue

        start = datetime.datetime.strptime(meeting_time, "%d/%m/%y %H:%M")
        end = start + datetime.timedelta(minutes=30)

        week_start_date = config.week_start_date
        week_end_date = config.week_end_date

        # Check if date is within the config's start and end date.
        if not (week_start_date <= start <= week_end_date):
            print("*" * 5, "Date is not within the week start and end dates: {}".format(start))
            continue

        print("Start: {}".format(start))
        print("End: {}".format(end))

        if not dry_run:
            if not (user_a and user_b):
                print("*" * 5, "User's are not present")
                continue

            meeting = services.create_meeting(
                config=config,
                start=start,
                end=end,
                participants=[user_a, user_b]
            )

            print("Created Meeting for users {} & {}: {}".format(email_a, email_b, meeting.id))

        print("End", "-" * 80)


def _check_if_users_had_a_meeting(user_a, user_b):
    """Check if user's have already met.
    
    Returns:
        The common meeting ids for both users.

    """
    meetings_a = user_a.meeting_set.exclude(
        status=choices.MEETING_STATUS_CANCELLED
    ).values_list("id", flat=True)
    meetings_b = user_b.meeting_set.exclude(
        status=choices.MEETING_STATUS_CANCELLED
    ).values_list("id", flat=True)

    return set(meetings_a) & set(meetings_b)
