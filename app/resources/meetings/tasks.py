import datetime
import logging
import pytz
from copy import copy

from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from freelance.settings import TIME_ZONE, CONTACT_US_URL, WEBSITE_URL, FRONT_URL
from integrations.freshchat import public as freshchat_public
from resources.meetings import choices
from resources.meetings import models
from resources.meetings import services
from resources.meetings import signals
from integrations.google import public as google_public
from django.contrib.auth import get_user_model
from rewards.services import get_max_rewards_rs_conversion
from points import models as points_models


@periodic_task(run_every=crontab(day_of_week='sunday', hour='17', minute='30'))
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
        week_start_date = timezone.now().date() + datetime.timedelta(days=8)
    if not week_end_date:
        week_end_date = week_start_date + datetime.timedelta(days=choices.DEFAULT_MEETING_WEEK_DURATION)
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
                'name': user.get_display_first_name()
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

        # Checking if profile exists.
        if not (p1.has_profile and p2.has_profile):
            continue

        display_day = meeting.time_slot.get_display_day()
        display_time = meeting.time_slot.get_display_time()

        subject = 'Introducing {} & {}'.format(
            p1.name.title(),
            p2.name.title()
        )
        to_emails = [p1.email, p2.email, choices.EXTRA_EMAIL_FOR_INTRO_VERIFICATION]
        # Populating data.
        data = {}
        p1_objective_one = None
        p1_objective_two = None
        p2_objective_one = None
        p2_objective_two = None

        p1_prefs = p1.meeting_preferences.filter(meeting=meeting.config).last()
        p2_prefs = p2.meeting_preferences.filter(meeting=meeting.config).last()

        if p1_prefs:
            p1_objective_one = p1_prefs.objectives.filter(type=choices.OBJECTIVE_TYPES[1][0]).first().name
            p1_objective_two = p1_prefs.objectives.filter(type=choices.OBJECTIVE_TYPES[0][0]).first().name

        if p2_prefs:
            p2_objective_one = p2_prefs.objectives.filter(type=choices.OBJECTIVE_TYPES[1][0]).first().name
            p2_objective_two = p2_prefs.objectives.filter(type=choices.OBJECTIVE_TYPES[0][0]).first().name

        for email in to_emails:
            data[email] = {
                'day': display_day,
                'time': display_time,
                'name_a': p1.get_display_first_name(),
                'name_b': p2.get_display_first_name(),
                'link': meeting.link,
                'introduction_a': p1.profile.get_introduction(),
                'introduction_b': p2.profile.get_introduction(),
                'linkedin_a': p1.profile.linkedin_url,
                'linkedin_b': p2.profile.linkedin_url,
                **({'objective_one_a': p1_objective_one} if p1_objective_one is not None else {}),
                **({'objective_two_a': p1_objective_two} if p1_objective_two is not None else {}),
                **({'objective_one_b': p2_objective_one} if p2_objective_one is not None else {}),
                **({'objective_two_b': p2_objective_two} if p2_objective_two is not None else {}),
                'contact_us': CONTACT_US_URL,
                'website_url': WEBSITE_URL,
            }

        from_email = choices.MEETING_COMMUNICATION_FROM_EMAIL
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


@periodic_task(run_every=crontab(day_of_week='wednesday', hour='18', minute='30'))
def send_active_meetings_data_to_analytics(meetings=None):
    """Sending active meeting data to Analytics platforms.

    Args:
        meetings(list/queryset): Meeting object queryset.

    """
    meetings = meetings if meetings else services.get_active_meetings()
    for meeting in meetings:
        participants = meeting.participants.all()
        participants_emails = list(participants.values_list('email', flat=True))
        for participant in meeting.participants.all():
            signals.new_meeting_created.send(
                sender=meeting.__class__,
                user=participant,
                time_slot=meeting.time_slot.__str__(),
                participants=participants_emails,
                meeting_config=meeting.meeting_config.__str__(),
                meeting_link=meeting.link
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

    start_time = (now_time + datetime.timedelta(minutes=135)).time()
    end_time = (now_time + datetime.timedelta(minutes=150)).time()
    # Getting date for the estimated start_time of the meeting.
    date = (now_time + datetime.timedelta(minutes=150)).date()

    meetings = models.Meeting.objects.filter(
        config__is_active=True,
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


@periodic_task(run_every=crontab(minute='*/15'))
def send_1_on_1_feedback_emails(meetings=None):
    """Send feedback mails for 1:1 meetings after 90 minutes of the
        meeting.

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    start_time = (now_time - datetime.timedelta(minutes=105)).time()
    end_time = (now_time - datetime.timedelta(minutes=90)).time()
    # Getting date for the estimated end_time of the meeting.
    date = (now_time - datetime.timedelta(minutes=90)).date()

    meetings = models.Meeting.objects.filter(
        config__is_active=True,
        is_canceled=False,
        time_slot__date=date,
        time_slot__end_time__gte=start_time,
        time_slot__end_time__lt=end_time
    ) if not meetings else meetings

    logging.info("Sending feedback emails for meetings between {} - {}. Meetings count: {}".format(
            start_time, end_time, meetings.count()
    ))

    for meeting in meetings:
        if not meeting.participants.count() == choices.MAX_MEMBER_FOR_ONE_ON_ONE:
            continue

        p1 = meeting.participants.all()[0]
        p2 = meeting.participants.all()[1]

        # Checking if profile exists.
        subject = 'How was your 1:1 meeting?'

        to_emails = [p1.email, p2.email]
        from_email = choices.MEETING_COMMUNICATION_FROM_EMAIL

        template_name = choices.ONE_ON_ONE_FEEDBACK_EMAIL_TEMPLATE

        # Sending the emails.
        for to in to_emails:
            p1.send_email(
                subject=subject,
                to=[to],
                template_name=template_name,
                content={},
                from_email=from_email,
                merge_vars={
                    to: {'email': to}
                }
            )


# TODO(Abhishek) - Deprecate once we move to new message with Rsvp link
def send_whatsapp_1_on_1_meeting_time_confirmation(meetings=None):
    """Send confirmation of time slot whatsapp message to meeting participants

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    meetings = services.get_active_meetings() if not meetings else meetings

    local_tz = pytz.timezone(TIME_ZONE)

    for meeting in meetings:
        for participant in meeting.participants.all():
            if meeting.start and meeting.end:
                local_start_datetime = meeting.start.replace(tzinfo=pytz.utc).astimezone(local_tz)
                local_end_datetime = meeting.end.replace(tzinfo=pytz.utc).astimezone(local_tz)
            else:
                local_start_datetime = datetime.datetime.combine(meeting.time_slot.date, meeting.time_slot.start_time)
                local_end_datetime = datetime.datetime.combine(meeting.time_slot.date, meeting.time_slot.end_time)

            freshchat_public.send_meeting_time_confirmation(
                participant,
                local_start_datetime,
                local_end_datetime
            )


def send_whatsapp_1_on_1_rsvp_confirmation(meetings=None):
    """ Send whatsapp with rsvp link to all active meetings

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    meetings = services.get_active_meetings() if not meetings else meetings

    for meeting in meetings:
        for rsvp in meeting.rsvps.all():
            if rsvp.status == choices.MEETING_RSVP_STATUS_PENDING:
                freshchat_public.send_meeting_confirmation_rsvp(
                    user=rsvp.participant,
                    meeting=meeting,
                )


@periodic_task(run_every=crontab(hour=11, minute=30))
def send_whatsapp_1_on_1_rsvp_reminder(meetings=None):
    """ Send whatsapp reminder with Rsvp link
    
    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    # Getting date for the for next day.
    date = (now_time + datetime.timedelta(days=1)).date()

    meetings = models.Meeting.objects.filter(
        config__is_active=True,
        is_canceled=False,
        time_slot__date=date,
    ) if not meetings else meetings

    logging.info("Sending rsvp reminders for meetings on {}. Meetings count: {}".format(
        date, meetings.count()
    ))

    for meeting in meetings:
        for rsvp in meeting.rsvps.all():
            # Dont send whatsapp if rsvp status is not pending
            if not rsvp.status == choices.MEETING_RSVP_STATUS_PENDING:
                continue

            freshchat_public.send_meeting_rsvp_reminder(rsvp.participant, meeting)


@periodic_task(run_every=crontab(minute='*/15'))
def update_meeting_rsvp_status_from_google(meetings=None):
    """
    Update the Meetings Rsvp Status for participants of all upcoming meetings

    meetings(Meeting queryset): Queryset of meeting you want to update rsvp status for
        participants.

    """
    meetings = services.get_active_meetings() if not meetings else meetings

    for meeting in meetings:
        for rsvp in meeting.rsvps.all():

            # Dont update data if rsvp status is attending
            if rsvp.status == choices.MEETING_RSVP_STATUS_ATTENDING:
                continue
            google_public.get_and_update_rsvp_status(rsvp)


@periodic_task(run_every=crontab(hour=2, minute=30))
def cancel_meetings_for_no_rsvp(meetings=None):
    """ Cancel meetings if participant rsvp status is pending or not attending

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to cancel.

    """
    today = datetime.datetime.now().date()

    meetings = models.Meeting.objects.filter(
        config__is_active=True,
        is_canceled=False,
        time_slot__date=today,
    ) if not meetings else meetings

    for meeting in meetings:
        for rsvp in meeting.rsvps.all():
            if rsvp.status in choices.MEETING_RSVP_UNCONFIRMED_STATUSES:
                meeting.is_canceled = True
                meeting.save()
                _send_meeting_cancellation_email(meeting)
                break


@periodic_task(run_every=crontab(day_of_week='monday', hour=2, minute=30))
def send_weekly_meeting_rewards_email(users=None):
    users = get_user_model().objects.all() if not users else users

    meeting_points_value = points_models.PointsRule.objects.get(key=15).points_value

    for user in users:
        now = datetime.datetime.now().date()
        week_start_date = now - datetime.timedelta(days=7)
        week_end_date = now - datetime.timedelta(days=1)

        meetings = user.meeting_set.filter(
            is_canceled=False,
            time_slot__date__gte=week_start_date,
            time_slot__date__lte=week_end_date,
        )

        # If no meetings last week. continue
        if not meetings:
            continue

        # Send email to user
        subject = 'You have earned new rewards'
        template = choices.MEETING_WEEKLY_REWARDS_TEMPLATE
        from_email = choices.MEETING_REWARDS_FROM_EMAIL
        rewards_link = ''

        max_conversion = get_max_rewards_rs_conversion()
        week_rs_value = int(len(meetings) * meeting_points_value * max_conversion)
        total_points = user.points.points
        total_rs_value = int(user.points.points * max_conversion)

        data = {user.email: {
            'week_rs_value': week_rs_value,
            'total_points': total_points,
            'total_rs_value': total_rs_value,
            'contact_us': CONTACT_US_URL,
            'website_url': WEBSITE_URL,
            'rewards_link': rewards_link,
        }}

        user.send_email(
            subject=subject,
            template_name=template,
            to=[user.email],
            from_email=from_email,
            content={},
            merge_vars=data,
        )


def _send_meeting_cancellation_email(meeting):
    """ Sends meeting cancellation email for meeting

    Args:
        meeting(Meeting): Meeting object to send email for

    """

    # For one on one meetings there are only two participants
    # allowed.
    if not meeting.participants.count() == choices.MAX_MEMBER_FOR_ONE_ON_ONE:
        return

    p1_rsvp = meeting.rsvps.all()[0]
    p2_rsvp = meeting.rsvps.all()[1]

    p1_rsvp_declined = p1_rsvp.status in choices.MEETING_RSVP_UNCONFIRMED_STATUSES
    p2_rsvp_declined = p2_rsvp.status in choices.MEETING_RSVP_UNCONFIRMED_STATUSES

    to_emails = [p1_rsvp.participant.email, p2_rsvp.participant.email, choices.EXTRA_EMAIL_FOR_INTRO_VERIFICATION]
    subject = "1:1 Meeting Cancelled"
    template = choices.ONE_ON_ONE_MEETING_CANCELED_TEMPLATE
    display_day = meeting.time_slot.get_display_day()
    display_time = meeting.time_slot.get_display_time()

    if p1_rsvp_declined and p2_rsvp_declined:
        declined_string = "{} & {}".format(p1_rsvp.participant.email, p2_rsvp.participant.email)
    elif p1_rsvp_declined:
        declined_string = p1_rsvp.participant.email
    else:
        declined_string = p2_rsvp.participant.email

    message_link = 'https://{}/dashboard/inbox'.format(FRONT_URL)
    rsvp_link = 'https://{}/meetings/'.format(FRONT_URL)

    data = {}
    for email in to_emails:
        data[email] = {
            'day': display_day,
            'time': display_time,
            'declined_users': declined_string,
            'message_link': message_link,
            'rsvp_link': rsvp_link,
            'contact_us': CONTACT_US_URL,
            'website_url': WEBSITE_URL,
        }

    from_email = choices.MEETING_COMMUNICATION_FROM_EMAIL
    # reply_to_emails is all to_emails plus the from_email.
    reply_to_emails = copy(to_emails)
    reply_to_emails.append(from_email)

    for to in to_emails:
        reply_to = copy(reply_to_emails)
        # Popping the to email from reply_to emails.
        reply_to.pop(reply_to_emails.index(to))
        p1_rsvp.participant.send_email(
            subject=subject,
            template_name=template,
            to=[to],
            from_email=from_email,
            content={},
            merge_vars=data,
            reply_to=reply_to,
        )
