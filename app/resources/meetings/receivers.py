import datetime
from copy import copy

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from freelance.settings import FRONT_URL, WEBSITE_URL, CONTACT_US_URL
from resources.meetings import models
from resources.meetings import services
from resources.meetings import signals
from resources.meetings import choices
from consumers.chat import signals as chat_signals
from users import services as users_services
from django.contrib.auth import get_user_model

MEETING_ADD_USER_POINTS_KEY = 15


@receiver(post_save, sender=models.MeetingPreference)
def send_analytics_for_user_meeting_preference(sender, instance, created, *args, **kwargs):
    time_slots = instance.time_slots.all()
    all_time_slots = []
    for time_slot in time_slots:
        slot = {
            'start_time': str(time_slot.start_time),
            'end_time': str(time_slot.end_time),
            'date': str(time_slot.date)}
        all_time_slots.append(slot)

    signals.registered_for_meeting.send(
        sender=instance,
        user=instance.user,
        meeting=instance.meeting.pk,
        created=created,
        week_start_date=str(instance.meeting.week_start_date),
        week_end_date=str(instance.meeting.week_end_date),
        number_of_meetings=instance.number_of_meetings,
        interests=[interest.name for interest in instance.interests.all()],
        objective=instance.objective,
        time_slots=all_time_slots
    )


@receiver(post_save, sender=models.Config)
def send_analytics_for_meeting_config_creation(sender, instance, created, *args, **kwargs):
    if not created:
        return

    time_slots = instance.available_time_slots.all()
    all_time_slots = []
    for time_slot in time_slots:
        slot = {
            'start_time': str(time_slot.start_time),
            'end_time': str(time_slot.end_time),
            'date': str(time_slot.date)}
        all_time_slots.append(slot)

    signals.new_meeting_config_created.send(
        sender=instance,
        user=users_services.get_admin_user(),
        title=instance.title,
        week_start_date=str(instance.week_start_date),
        week_end_date=str(instance.week_end_date),
        registration_start_date=str(instance.registration_start_date),
        registration_end_date=str(instance.registration_end_date),
        time_slots=all_time_slots
    )


@receiver(signals.create_new_meeting_preference_typeform)
def create_meeting_preference_for_typeform_user(
        sender, user, time_preferences, interests, days, objective, *args, **kwargs
):
    clean_time_preferences = []
    for time_preference in time_preferences:
        clean_time_preferences.append(_clean_time_preference(time_preference))
    # Was adding users to the previous config according to the scripts.
    # Changed it to add user's to current meeting.
    meeting_config = services.get_latest_active_meeting_config()
    # Get respective objectives for User Meeting Preference.
    objective_objs = models.Objective.objects.filter(name__in=objective)

    # Calculate time slots for the data provided.
    start_date = meeting_config.week_start_date
    end_date = meeting_config.week_end_date

    end_date_weekday = end_date.weekday()

    dates = []
    for day in days:
        if day == 'Thursday':
            day_weekday = 3
        else:
            day_weekday = 4

        date_diff = end_date_weekday - day_weekday
        date = end_date - datetime.timedelta(days=date_diff)
        dates.append(date)

    user_time_slots = []

    for date in dates:
        for time_preference in clean_time_preferences:
            start, end = time_preference.split('-')
            start = int(start.strip()) + 12
            end = int(end.strip()) + 12
            start_time, end_time = datetime.time(start), datetime.time(end)
            time_slot, _ = models.TimeSlot.objects.get_or_create(
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            user_time_slots.append(time_slot)

    meeting_preference, _ = models.MeetingPreference.objects.get_or_create(
        meeting=meeting_config,
        user=user,
    )

    for obj in objective_objs:
        meeting_preference.objectives.add(obj)

    interests = models.Interest.objects.filter(
        name__in=interests
    )
    for interest in interests or []:
        meeting_preference.interests.add(interest)
    for slot in user_time_slots or []:
        meeting_preference.time_slots.add(slot)


@receiver(m2m_changed, sender=models.Meeting.participants.through)
def create_meeting_for_users(sender, instance, *args, **kwargs):
    if kwargs.get('action') == 'post_add':
        for participant in kwargs['pk_set']:
            try:
                user = get_user_model().objects.get(pk=participant)
                signals.new_user_assigned_to_meeting.send(
                    sender=instance,
                    user=user,
                    rule_key=MEETING_ADD_USER_POINTS_KEY,
                    base_factor=1,
                )
            except get_user_model().DoesNotExist:
                continue

            models.MeetingRSVP.objects.create(
                meeting=instance,
                participant_id=participant,
            )

        chat_signals.create_chat_for_meeting.send(
            sender=instance,
            participants=instance.participants.all(),
        )


@receiver(signals.rsvp_status_updated)
def update_meeting_status_on_rsvp_update(sender, user, rsvp, *args, **kwargs):
    """Update meeting status based on meeting rsvp status update."""
    meeting = rsvp.meeting

    if rsvp.status == choices.MEETING_RSVP_STATUS_NOT_ATTENDING:
        meeting.status = choices.MEETING_STATUS_CANCELLED
        meeting.save()

    if rsvp.status == choices.MEETING_RSVP_STATUS_RESCHEDULE:
        meeting.status = choices.MEETING_STATUS_RESCHEDULED
        meeting.save()

    if rsvp.status == choices.MEETING_RSVP_STATUS_ATTENDING:
        other_rsvp = meeting.rsvps.all().exclude(id=rsvp.id).first()
        if not other_rsvp:
            return
        if other_rsvp.status == choices.MEETING_RSVP_STATUS_ATTENDING:
            # Setting meeting status confirmed if both user's have confirmed.
            meeting.status = choices.MEETING_STATUS_CONFIRMED
            meeting.save()


@receiver(signals.reschedule_request_approved)
def create_new_meeting_on_reschedule_request_approval(sender, reschedule_request, time_slot, *args, **kwargs):
    """Create new meeting between participants once reschedule request is approved.

    Args:
        reschedule_request(RescheduleRequest): reschedule request approved.
        time_slot(datetime.datetime): time_slot decided for the rescheduled meeting.

    """
    old_meeting = reschedule_request.old_meeting
    # Updating the status of old meeting.
    old_meeting.status = choices.MEETING_STATUS_CANCELLED
    old_meeting.is_canceled = True
    old_meeting.save()

    start = time_slot
    end = time_slot + timezone.timedelta(minutes=30)
    config = services.get_config_for_date(time_slot.date())

    new_meeting = services.create_meeting(
        config=config,
        participants=old_meeting.participants.all(),
        start=start,
        end=end,
        status=choices.MEETING_STATUS_CONFIRMED
    )

    reschedule_request.new_meeting = new_meeting
    reschedule_request.save()


@receiver(signals.reschedule_request_declined)
def cancel_meeting_on_reschedule_request_declined(sender, reschedule_request, *args, **kwargs):
    """Cancel old meeting between participants once reschedule request is declined.

    Args:
        reschedule_request(RescheduleRequest): reschedule request declined.

    """
    meeting = reschedule_request.old_meeting
    meeting.status = choices.MEETING_STATUS_CANCELLED
    meeting.save()


@receiver(post_save, sender=models.MeetingRSVP)
def on_save_meeting_rsvp(sender, instance, created, *args, **kwargs):
    meeting = instance.meeting
    all_attending = True

    for rsvp in meeting.rsvps.all():
        if rsvp.status in choices.MEETING_RSVP_UNCONFIRMED_STATUSES:
            all_attending = False

    # If all users for meeting are not attending meeting, return
    if not all_attending:
        return

    # Send meeting confirmed email to all participants
    meeting.status = choices.MEETING_STATUS_CONFIRMED
    meeting.save()


@receiver(post_save, sender=models.Meeting)
def check_and_send_confirmed_meeting_email(sender, instance, created, *args, **kwargs):
    previous_status = instance._Meeting__previous_status
    current_status = instance.status

    # If meeting is not confirmed, return
    if current_status != choices.MEETING_STATUS_CONFIRMED:
        return

    if previous_status == choices.MEETING_STATUS_CONFIRMED:
        return

    _send_meeting_confirmed_email(instance)


@receiver(post_save, sender=models.RescheduleRequest)
def update_meeting_status_to_rescheduled(sender, instance, created, *args, **kwargs):
    """When a reschedule request is raised, update the meeting status as well."""
    if not created:
        return

    creator = instance.requested_by
    meeting = instance.old_meeting
    rsvp = creator.meeting_rsvps.filter(meeting=meeting).last()
    rsvp.status = choices.MEETING_RSVP_STATUS_RESCHEDULE
    rsvp.save()
    
    meeting.status = choices.MEETING_STATUS_RESCHEDULED
    meeting.save()


# --------------- PRIVATE FUNCTIONS ----------------- #
def _send_meeting_confirmed_email(meeting):
    """ Sends meeting confirmed email to all participants

    Args:
        meeting(Meeting): Meeting for which confirmation email is sent

    """

    # For one on one meetings there are only two participants
    # allowed.
    if not meeting.participants.count() == choices.MAX_MEMBER_FOR_ONE_ON_ONE:
        return

    p1 = meeting.participants.all()[0]
    p2 = meeting.participants.all()[1]

    subject = "1:1 Meeting Confirmed"
    to_emails = [p1.email, p2.email, choices.EXTRA_EMAIL_FOR_INTRO_VERIFICATION]

    message_link = 'https://{}/dashboard/inbox'.format(FRONT_URL)
    display_day = meeting.time_slot.get_display_day()
    display_time = meeting.time_slot.get_display_time()

    data = {}
    for email in to_emails:
        data[email] = {
            'day': display_day,
            'time': display_time,
            'link': meeting.link,
            'message_link': message_link,
            'meeting_link': meeting.link,
            'contact_us': CONTACT_US_URL,
            'website_url': WEBSITE_URL,
        }

    from_email = choices.MEETING_COMMUNICATION_FROM_EMAIL

    # reply_to_emails is all to_emails plus the from_email.
    reply_to_emails = copy(to_emails)
    reply_to_emails.append(from_email)

    template_name = choices.ONE_ON_ONE_MEETING_CONFIRMED_TEMPLATE

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


REMOVE_CHARS = ['PM', 'pm', 'Pm', 'pM', 'p.m.', 'p.m', 'P.M.', 'P.M', 'P.m.', 'P.m']


def _clean_time_preference(time_preference):
    for i in REMOVE_CHARS:
        time_preference = time_preference.replace(i, '')
    return time_preference
