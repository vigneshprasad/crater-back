import datetime

from celery.schedules import crontab
from django.utils import timezone

from freelance.celery import app
from resources.meetings import services
from resources.meetings import choices


@app.task(crontab(day_of_week='sunday', hour='0', minute='0'))
def create_weekly_one_on_one_meeting():
    week_start_date = timezone.now().date()
    week_end_date = week_start_date + datetime.timedelta(days=6)

    new_time_slots = services.create_default_time_slots(week_start_date, week_end_date)

    title = choices.DEFAULT_ONE_ON_ONE_MEETING_TITLE
    services.create_meetings_for_time_period(
        week_start_date,
        week_end_date,
        time_slots=new_time_slots,
        title=title
    )


@app.task(crontab(hour='0', minute='0'))
def close_last_weeks_meetings():
    meetings = services.get_old_active_meetings()
    for meeting in meetings:
        meeting.close_meeting()
