import datetime

from django.utils import timezone
from cryptography.fernet import Fernet

from freelance.settings import FERNET_KEY
from resources.meetings import models
from resources.meetings import choices
from resources.meetings import serializers
from users import services as user_services
from django.contrib.auth import get_user_model
from integrations.google import public


def get_objectives_list():
    objectives = [{
        'key': objective[0],
        'label': objective[1] 
    } for objective in choices.OBJECTIVE_CHOICES]
    return objectives


def get_interest_list():
    interests = models.Interest.objects.filter(is_active=True)
    data = []
    for interest in interests:
        data.append({
            "pk": interest.pk,
            "name": interest.name,
            "icon": interest.icon.url if interest.icon else None,
        })
    return data


def create_meeting_config_for_time_period(
        start_date,
        end_date,
        title=choices.DEFAULT_MEETING_TITLE,
        time_slots=None,
        registration_start_date=None,
        registration_end_date=None
):
    """
    Creates meeting config object for a give time period.

    Args:
        start_date(Date): Meeting start date.
        end_date(Date): Meeting end date.
        title(Char): Meeting title. Not required since
            default is provided.
        time_slots(list(TimeSlot)): List of TimeSlots objects
            for the meeting. If not provided these are created
            with a set of default time slots.
        registration_start_date(Date): When does meeting
            registration start.
        registration_end_date(Date): Meeting registration closing
            date.

    Returns:
        Created MeetingConfig object.

    Note:
        registration_start_date can be less than week_start_date.



    """
    if not time_slots:
        time_slots = create_default_time_slots(start_date, end_date)

    # If registration end date is not present, week end
    # is taken as default registration end date.
    if not registration_start_date:
        registration_start_date = start_date

    if not registration_end_date:
        registration_end_date = end_date

    meeting_config, _ = models.Config.objects.get_or_create(
        week_start_date=start_date,
        week_end_date=end_date,
        registration_start_date=registration_start_date,
        registration_end_date=registration_end_date,
        title=title
    )
    # Added time slots to the meeting object.
    meeting_config.available_time_slots.add(*time_slots)

    return meeting_config


def create_default_time_slots(start_date, end_date):
    """
    Create default time slots for given start and end dates.

    Args:
        start_date(Date)
        end_date(Date)

    Returns:
        time_slots(list(TimeSlot)): List of time slots created
            for the given start and end dates.

    """

    all_time_slots = []
    date = start_date

    while date <= end_date:
        weekday = date.weekday()
        time_slots_for_weekday = choices.DEFAULT_DISPLAY_TIME_SLOTS.get(weekday)

        # If there are no time slots for that date, increment the date.
        if not time_slots_for_weekday:
            date += datetime.timedelta(days=1)
            continue

        time_slots = _create_time_slots_for_date_and_slots(date, time_slots_for_weekday)
        all_time_slots += time_slots
        date += datetime.timedelta(days=1)

    return all_time_slots


def _create_time_slots_for_date_and_slots(date, time_slots):
    """
    Create time slots for a particular date and time slots
    info.

    Args:
        date(Date): Date for which time slots are being
            created.
        time_slots(list(dict)): List of dictionaries with
            start_time and end_time.
            [{
                'start_time': time(12, 00, 00),
                'end_time': time(12, 30, 00)
            }]

    Returns:
        slots(list(TimeSlots)): Returns a list of time slots
            created.

    """
    slots = []

    for time_slot in time_slots:
        # Creating start and end datetime fields as well.
        start = datetime.datetime.combine(date=date, time=time_slot['start_time'])
        end = datetime.datetime.combine(date=date, time=time_slot['end_time'])
        slot, _ = models.TimeSlot.objects.get_or_create(
            date=date,
            start_time=time_slot['start_time'],
            end_time=time_slot['end_time'],
            start=start,
            end=end
        )
        slots.append(slot)

    return slots


def get_latest_old_meeting_config():
    """
    Returns last meeting config whose week_end_date
    is less than today i.e closed.

    return:
        Meeting object.

    """
    return models.Config.objects.filter(
        week_end_date__lt=timezone.now().date()
    ).order_by('-week_end_date').first()


def get_old_active_meeting_configs():
    """
    Returns active meeting configs whose week_end_date
    is less than today.

    return:
        Queryset of meetings.

    """
    return models.Config.objects.filter(
        is_active=True,
        week_end_date__lt=timezone.now().date()
    )


def get_meeting_configs_with_open_registration():
    """
    Get meetings configs with open registration.

    Return:
        Queryset of MeetingConfig object.

    """
    active_meeting_configs = get_active_meeting_configs()
    if not active_meeting_configs:
        return None
    return active_meeting_configs.filter(
        is_registration_open=True,
        registration_end_date__lte=timezone.now().date()
    )


def get_active_meeting_configs():
    """
    Get active meeting configs.

    Return:
        Queryset of MeetingConfig object.

    """
    return models.Config.objects.filter(
        week_end_date__gte=datetime.datetime.now().date(),
        is_active=True
    )


def get_latest_active_meeting_config():
    """
    Get current week active meeting config
    (Used for Meeting Preferences Api and meeting config Api)

    Returns:
        Queryset of MeetingConfig object.
    """
    active_meeting_configs = get_active_meeting_configs()
    if not active_meeting_configs:
        return None
    return active_meeting_configs.last()


def get_current_week_meeting_config():
    """
    Get latest active meeting configs.

    Return:
        Queryset of MeetingConfig object.

    """
    now = datetime.datetime.now().date()
    start = now - datetime.timedelta(days=now.weekday())
    end = start + datetime.timedelta(days=6)
    active_meeting_configs = get_active_meeting_configs()
    if not active_meeting_configs:
        return None
    return active_meeting_configs.filter(
        week_start_date__gte=start,
        week_end_date__lte=end,
    ).last()


def get_active_meetings(start_date=None, end_date=None):
    """
    Get all meetings that are active in a given duration.

    Args:
        start_date(date): Start date for the meetings.
        end_date(date): End date for meetings.

    Return:
        Queryset of Meeting object.

    """
    latest_active_meeting_config = get_current_week_meeting_config()
    if not latest_active_meeting_config:
        return []
    # Taking start and end date from the latest meeting config which is
    # active.
    if not start_date:
        start_date = latest_active_meeting_config.week_start_date
    if not end_date:
        end_date = latest_active_meeting_config.week_end_date

    # TODO(Nishant): Figure out a better way to query for active/inactive meetings.
    return models.Meeting.objects.filter(
        config__is_active=True,
        start__gte=start_date,
        end__lte=end_date
    ).exclude(status=choices.MEETING_STATUS_CANCELLED)


def get_opted_in_users_for_config(config=None):
    """Get opted in users for a meeting config.

    Args:
        config(Config): Get opted in user's for a config

    """
    latest_config = get_latest_active_meeting_config() if not config else config
    opted_in_user_ids = models.MeetingPreference.objects.filter(
        meeting=latest_config
    ).values_list('user_id', flat=True)
    return user_services.get_users_for_ids(list(opted_in_user_ids))


def get_opted_in_user_for_meetings(meeting_type=choices.MEETING_CHOICE_1_ON_1):
    """
    Get opted in user for a type of meeting.

    Args:
        meeting_type(str): Type of meeting.

    Return:
        List of users opted in for the type of meeting.

    """
    meeting_preference_user_ids = models.MeetingPreference.objects.filter(
        meeting__type=meeting_type
    ).values_list('user_id', flat=True)

    # Creating a set.
    user_ids = set(meeting_preference_user_ids)

    meeting_user_ids = models.Meeting.objects.filter(
        config__type=meeting_type
    ).values_list('participants', flat=True)
    # Updating the set with meeting_user_ids.
    user_ids.update(meeting_user_ids)

    return user_services.get_users_for_ids(list(user_ids))


def get_meeting_config_time_slots(meeting):
    all_slots = meeting.available_time_slots.all()
    available_slots = {}
    for slot in all_slots:
        date_str = str(slot.date)
        if not available_slots.get(date_str):
            available_slots[date_str] = []
        available_slots[date_str].append({
            'pk': slot.pk,
            'start': slot.start_time,
            'end': slot.end_time
        })
    return available_slots


def get_latest_meeting_preference(user):
    return models.MeetingPreference.objects.filter(user=user).last()


def get_user_meeting_from_url(query):
    """
    Get user and meeting object from the query string param of the url

    Args:
        query(String): query param from url created

    Returns:
        user(User): User object reference for rsvp
        meeting(Meeting): Meeting object reference for rsvp

    """
    f = Fernet(FERNET_KEY)
    decrypted_message = f.decrypt(query.encode()).decode()
    [user_id, meeting_id] = decrypted_message.split('|')
    try:
        user = get_user_model().objects.get(pk=user_id)
        meeting = models.Meeting.objects.get(pk=meeting_id)
        return user, meeting
    except models.Meeting.DoesNotExist:
        raise models.Meeting.DoesNotExist
    except get_user_model().DoesNotExist:
        raise get_user_model().DoesNotExist


def get_objectives_for_rsvp(rsvp):
    """
    Returns list of Meeting objective for meeting preference with same config as rsvp

    Args:
        rsvp(MeetingRsvp): Meeting RSVP object

    Returns:
        Serialized List of Meeting objectives

    """
    preference = models.MeetingPreference.objects.filter(
        user=rsvp.participant,
        meeting=rsvp.meeting.config,
    ).first()
    if not preference:
        return []

    objectives = preference.objectives
    serialized = serializers.MeetingObjectiveSerializer(objectives, many=True)
    return serialized.data


def get_interests_for_rsvp(rsvp):
    """
    Returns list of Meeting Interests for meeting preference with same config as rsvp

    Args:
        rsvp(MeetingRsvp): Meeting RSVP object

    Returns:
        Serialized List of Meeting interests

    """
    preference = models.MeetingPreference.objects.filter(
        user=rsvp.participant,
        meeting=rsvp.meeting.config,
    ).first()
    if not preference:
        return []

    interests = preference.interests
    serialized = serializers.MeetingInterestSerializer(interests, many=True)
    return serialized.data


def get_meeting_participant_with_rsvp(meeting):
    data = []
    for participant in meeting.participants.all():
        participant_data = serializers.MeetingUserSerializer(participant).data
        objectives = []
        interests = []

        try:
            rsvp = models.MeetingRSVP.objects.get(participant=participant, meeting=meeting)
            objectives = get_objectives_for_rsvp(rsvp)
            interests = get_interests_for_rsvp(rsvp)
            rsvp_data = serializers.MeetingRSVPSerializer(rsvp).data

        except models.MeetingRSVP.DoesNotExist:
            rsvp_data = None

        data.append({
            **participant_data,
            'rsvp': rsvp_data,
            'objectives': objectives,
            'interests': interests,
        })

    return data


def create_meeting(config, participants, start, end, status=choices.MEETING_STATUS_PENDING):
    """Creates meeting between participants.

    Args:
        config(Config): Meeting config for which the meeting should be
            created for.
        participants(list): list of users, participants of the meeting.
        start(datetime.datetime): starting datetime of the meeting.
        end(datetime.datetime): ending datetime of the meeting.
        status(str): status of the meeting being setup. If not provided
            default pending status is used.

    """
    meeting = models.Meeting.objects.create(
        config=config,
        start=start,
        end=end,
        status=status
    )
    for participant in participants:
        meeting.participants.add(participant)

    meeting_link = public.create_calendar_event_for_meeting(meeting)
    meeting.link = meeting_link
    meeting.save()

    return meeting


def get_config_for_date(date):
    """Returns correct config for a date."""
    config = models.Config.objects.filter(
        week_start_date__lte=date,
        week_end_date__gte=date,
        is_active=True
    ).first()

    return config if config else get_current_week_meeting_config()


def get_reschedule_from_url(query):
    """
    Get user and meeting object from the query string param of the url

    Args:
        query(String): query param from url created

    Returns:
        user(User): User object reference for rsvp
        reschedule(RescheduleRequest): RescheduleRequest object reference

    """
    f = Fernet(FERNET_KEY)
    decrypted_message = f.decrypt(query.encode()).decode()
    [user_id, reschedule_id] = decrypted_message.split('|')
    try:
        user = get_user_model().objects.get(pk=user_id)
        reschedule = models.RescheduleRequest.objects.get(pk=reschedule_id)
        return user, reschedule
    except models.RescheduleRequest.DoesNotExist:
        raise models.RescheduleRequest.DoesNotExist
    except get_user_model().DoesNotExist:
        raise get_user_model().DoesNotExist

def get_user_from_opt_in_url(query):
    """
    Get user and meeting object from the query string param of the url

    Args:
        query(String): query param from url created

    Returns:
        user(User): User object reference for rsvp
        reschedule(RescheduleRequest): RescheduleRequest object reference

    """
    f = Fernet(FERNET_KEY)
    user_id = f.decrypt(query.encode()).decode()
    try:
        user = get_user_model().objects.get(pk=user_id)
        return user
        
    except get_user_model().DoesNotExist:
        raise get_user_model().DoesNotExist
