import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from resources.meetings import services
from resources.meetings import choices


# @periodic_task(run_every=crontab(day_of_week='sunday', hour='19', minute='00'))
def create_weekly_one_on_one_meeting_config(
        week_start_date=None,
        week_end_date=None,
        time_slots=None
):
    """
    Creates weekly meeting and default time slots for that
    meeting.

    Args:
        week_start_date(Date): Week start date.
        week_end_date(Date): Week end date.
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
    if not week_start_date:
        week_start_date = timezone.now().date() + datetime.timedelta(days=1)
    if not week_end_date:
        week_end_date = week_start_date + datetime.timedelta(days=5)
    # Registration starts a few days early.
    registration_start_date = week_start_date - datetime.timedelta(
        days=choices.DEFAULT_REGISTRATION_START_AND_WEEK_START_DELTA
    )
    registration_end_date = week_start_date + datetime.timedelta(
        days=choices.DEFAULT_REGISTRATION_CLOSED_WEEKDAY
    )

    services.create_meeting_config_for_time_period(
        week_start_date,
        week_end_date,
        time_slots=time_slots,
        registration_start_date=registration_start_date,
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
    meeting_configs = services.get_old_active_meeting_configs()
    for meeting_config in meeting_configs:
        meeting_config.close_meeting()


# @periodic_task(crontab(hour='0', minute='0'))
def close_registration_for_last_weeks_meetings():
    """
    Closes registration for meetings with registration_end_date
    less than today.

    Runs everyday at 00:00 hour.

    """
    meeting_configs = services.get_meeting_configs_with_open_registration()
    for meeting_config in meeting_configs:
        meeting_config.close_registration()


def send_1_on_1_meeting_intro_emails(meetings):
    """Send intro for 1 on 1 meetings.

    Args:
        meetings(list/queryset): Meeting object queryset.

    """
    meetings = meetings if meetings else services.get_active_meetings()

    for meeting in meetings:
        # For one on one meetings there are only two participants
        # allowed.
        p1 = meeting.participants.all()[0]
        p2 = meeting.participants.all()[1]

        display_day = meeting.time_slot.get_display_day()
        display_time = meeting.time_slot.get_display_time()
        data = {
            p1.email: {
                'day': display_day,
                'time': display_time,
                'name_a': p1.name.title(),
                'name_b': p2.name.title(),
                'link': meeting.link,
                'introduction_a': p1.profile.get_introduction,
                'introduction_b': p2.profile.get_introduction,
                'linkedin_a': p1.profile.linkedin_url,
                'linkedin_b': p2.profile.linkedin_url,
            },
            p2.email: {
                'day': display_day,
                'time': display_time,
                'name_a': p1.name.title(),
                'name_b': p2.name.title(),
                'link': meeting.link,
                'introduction_a': p1.profile.get_introduction(),
                'introduction_b': p2.profile.get_introduction(),
                'linkedin_a': p1.profile.linkedin_url,
                'linkedin_b': p2.profile.linkedin_url,
            },
        }

        # Checking if profile exists.
        subject = 'Introducing {} & {}'.format(
            p1.name.title(),
            p2.name.title()
        )
        to = [p1.email, p2.email]
        template_name = choices.ONE_ON_ONE_INTRODUCTION_EMAIL_TEMPLATE

        # Sending the emails.
        p1.send_email(
            subject=subject,
            to=to,
            template_name=template_name,
            content={},
            from_email=choices.MEETINGS_FROM_EMAIL,
            merge_vars=data
        )
