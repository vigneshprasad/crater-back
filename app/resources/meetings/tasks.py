import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from resources.meetings import services
from resources.meetings import choices


# @periodic_task(run_every=crontab(day_of_week='sunday', hour='19', minute='00'))
def create_weekly_one_on_one_meeting(time_slots=None):
    """
    Creates weekly meeting and default time slots for that
    meeting.

    Args:
        time_slots(list(TimeSlots)): List of TimeSlots objects to
            be associated with the meeting. If not provided
            default time slots will be created.

    Notes:
        week_start_date will be that week's Monday.
        week_end_date will be that week's Saturday.
        registration_end_date(default) will be that
            week's Wednesday

    """
    title = choices.DEFAULT_ONE_ON_ONE_MEETING_TITLE
    # timezone.now() will provide Sunday's date. Since both are UTC.
    week_start_date = timezone.now().date() + datetime.timedelta(days=1)
    week_end_date = week_start_date + datetime.timedelta(days=5)

    registration_end_date = week_start_date + datetime.timedelta(
        days=choices.DEFAULT_REGISTRATION_CLOSED_WEEKDAY
    )

    services.create_meetings_for_time_period(
        week_start_date,
        week_end_date,
        time_slots=time_slots,
        registration_end_date=registration_end_date,
        title=title
    )


# @periodic_task(crontab(hour='0', minute='0'))
def close_last_weeks_meetings():
    """
    Closes meetings with week_end_date less
    than today.

    Runs everyday at 00:00 hour.

    """
    meetings = services.get_old_active_meetings()
    for meeting in meetings:
        meeting.close_meeting()


# @periodic_task(crontab(hour='0', minute='0'))
def close_registration_for_last_weeks_meetings():
    """
    Closes registration for meetings with registration_end_date
    less than today.

    Runs everyday at 00:00 hour.

    """
    meetings = services.get_meetings_with_open_registration()
    for meeting in meetings:
        meeting.close_registration()
