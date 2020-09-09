import datetime
import logging
from copy import copy

from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from integrations.freshchat import public as freshchat_public
from resources.meetings import choices
from resources.meetings import models
from resources.meetings import services
from resources.meetings import signals


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


def send_opt_in_reminder_for_new_meetings(opted_in_users=None):
    """
    Send emails reminding users to opt in for
    next 1:1 meeting.

    """
    opted_in_users = services.get_opted_in_user_for_meetings() \
        if not opted_in_users else opted_in_users
    template = choices.ONE_ON_ONE_OPT_IN_EMAIL_TEMPLATE
    for user in opted_in_users:
        data = {
            user.email: {
                'name': user.name.title()
            }
        }
        subject = "Signup for new connections this week"
        user.send_email(
            subject=subject,
            to=[user.email],
            template_name=template,
            content={},
            from_email=choices.MEETINGS_OPT_IN_FROM_EMAIL,
            merge_vars=data
        )


# Will run every Tuesday at 11 AM.
# @periodic_task(crontab(day_of_week='tuesday', hour='11', minute='00'))
def send_1_on_1_meeting_intro_emails(meetings=None):
    """Send intro for 1 on 1 meetings.

    Args:
        meetings(list/queryset): Meeting object queryset.

    """
    meetings = meetings if meetings else services.get_active_meetings()

    for meeting in meetings:
        # For one on one meetings there are only two participants
        # allowed.
        if not meeting.participants.count() == choices.MAX_MEMBER_FOR_ONE_ON_ONE:
            continue

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
                'introduction_a': p1.profile.get_introduction(),
                'introduction_b': p2.profile.get_introduction(),
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
            choices.EXTRA_EMAIL_FOR_INTRO_VERIFICATION: {
                'day': display_day,
                'time': display_time,
                'name_a': p1.name.title(),
                'name_b': p2.name.title(),
                'link': meeting.link,
                'introduction_a': p1.profile.get_introduction(),
                'introduction_b': p2.profile.get_introduction(),
                'linkedin_a': p1.profile.linkedin_url,
                'linkedin_b': p2.profile.linkedin_url,
            }
        }

        # Checking if profile exists.
        subject = 'Introducing {} & {}'.format(
            p1.name.title(),
            p2.name.title()
        )

        to_emails = [p1.email, p2.email, choices.EXTRA_EMAIL_FOR_INTRO_VERIFICATION]
        from_email = choices.MEETINGS_INTRO_FROM_EMAIL
        # reply_to_emails is all to_emails plus the from_email.
        reply_to_emails = copy(to_emails)
        reply_to_emails.append(from_email)

        template_name = choices.ONE_ON_ONE_INTRODUCTION_EMAIL_TEMPLATE

        # Sending the emails.
        for to in to_emails:
            reply_to = copy(reply_to_emails)
            # Popping the to email from reply_to emails.
            reply_to.pop(reply_to_emails.index(to))
            p1.send_email(
                subject=subject,
                to=[to],
                reply_to=reply_to,
                template_name=template_name,
                content={},
                from_email=from_email,
                merge_vars=data
            )


def send_active_meetings_data_to_analytics(meetings=None):
    """Sending active meeting data to Analytics platforms.

    Args:
        meetings(list/queryset): Meeting object queryset.

    """
    meetings = meetings if meetings else services.get_active_meetings()
    for meeting in meetings:
        participants = meeting.participants.all()
        participants_emails = participants.values_list('email', flat=True)
        for participant in meeting.participants.all():
            signals.new_meeting_created(
                sender=meeting.__class__,
                user=participant,
                time_slot=meeting.time_slot.__str__,
                participants=participants_emails,
                meeting_config=meeting.meeting_config.__str__,
                meeting_link=meeting.meeting_config
            )


# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
@periodic_task(run_every=crontab(minute='*/15'))
def send_whatsapp_meeting_reminders(meetings=None):
    """Sends whatsapp reminders for people 90 minutes before their meetings.

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    start_time = (now_time + datetime.timedelta(minutes=75)).time()
    end_time = (now_time + datetime.timedelta(minutes=90)).time()
    # Getting date for the estimated start_time of the meeting.
    date = (now_time + datetime.timedelta(minutes=90)).date()

    meetings = models.Meeting.objects.filter(
        meeting_config__is_active=True,
        is_canceled=False,
        time_slot__date=date,
        time_slot__start_time__gt=start_time,
        time_slot__start_time__lte=end_time
    ) if not meetings else meetings

    logging.info("Sending reminders for meetings between {} - {}. Meetings count: {}".format(
            start_time, end_time, meetings.count()
    ))

    for meeting in meetings:
        for participant in meeting.participants.all():
            freshchat_public.send_meeting_whatsapp_reminder_to_user(
                participant,
                meeting.time_slot.get_display_start_time()
            )


# @periodic_task(run_every=crontab(day_of_week='tuesday', hour='11', minute='00'))
def send_whatsapp_opt_ins_for_one_on_one_meetings(users=None):
    """Sends whatsapp messages for opting in for next weeks meetings.

    Args:
        users(User queryset): Queryset of user you want to send this
            message to. Added for testing.

    """
    users = services.get_opted_in_user_for_meetings() if not users else users
    # Logging info for users we are sending this to.
    logging.info('Sending opt-in messages to {} users'.format(len(users)))
    freshchat_public.send_meeting_opt_in_messages(users)
