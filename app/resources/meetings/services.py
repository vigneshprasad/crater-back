import datetime

from django.utils import timezone

from resources.meetings import models
from resources.meetings import choices
from tags import serializers as tags_serializers
from tags import models as tags_models
from users import services as user_services


def get_objectives_list():
    objectives = [{
        'key': objective[0],
        'label': objective[1] 
    } for objective in choices.OBJECTIVE_CHOICES]
    return objectives


def get_interest_list():
    interests = tags_serializers.InterestsSerializer(
        data=tags_models.Interests.objects.all(), many=True
    )
    interests.is_valid()
    return interests.data


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

    meeting_config, _ = models.MeetingConfig.objects.get_or_create(
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
        time_slots_for_weekday = choices.DEFAULT_TIME_SLOTS.get(weekday)

        if not time_slots_for_weekday:
            date += datetime.timedelta(days=1)
            continue
        time_slots = create_time_slots_for_date_and_slots(date, time_slots_for_weekday)

        for time_slot in time_slots:
            all_time_slots.append(time_slot)
        date += datetime.timedelta(days=1)

    return all_time_slots


def create_time_slots_for_date_and_slots(date, time_slots):
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

        slot, _ = models.TimeSlot.objects.get_or_create(
                date=date,
                start_time=time_slot['start_time'],
                end_time=time_slot['end_time']
        )
        slots.append(slot)

    return slots


def get_old_active_meeting_configs():
    """
    Closes meetings based on info provided
    in the model. (week_end_date)

    return:
        Queryset of meetings.

    """
    return models.MeetingConfig.objects.filter(
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
    return models.MeetingConfig.objects.filter(
        week_end_date__gte=datetime.datetime.now().date(),
        is_active=True
    )


def get_latest_active_meeting_config():
    """
    Get latest active meeting configs.

    Return:
        Queryset of MeetingConfig object.

    """
    active_meeting_configs = get_active_meeting_configs()
    if not active_meeting_configs:
        return None
    return active_meeting_configs.last()


def get_active_meetings(start_date=None, end_date=None):
    """
    Get all meetings that are active in a given duration.

    Args:
        start_date(date): Start date for the meetings.
        end_date(date): End date for meetings.

    Return:
        Queryset of Meeting object.

    """
    if not start_date:
        start_date = timezone.now().date() + datetime.timedelta(days=1)
    if not end_date:
        end_date = start_date + datetime.timedelta(days=3)

    return models.Meeting.objects.filter(
        meeting_config__is_active=True,
        time_slot__date__gte=start_date,
        time_slot__date__lte=end_date,
    )


def get_opted_in_user_for_meetings(meeting_type=choices.MEETING_CHOICE_1_ON_1):
    """
    Get opted in user for a type of meeting.

    Args:
        meeting_type(str): Type of meeting.

    Return:
        List of users opted in for the type of meeting.

    """
    meeting_preference_user_ids = models.UserMeetingPreference.objects.filter(
        meeting__type=meeting_type
    ).values_list('user_id', flat=True)
    # Creating a set.
    user_ids = set(meeting_preference_user_ids)
    meeting_user_ids = models.Meeting.objects.filter(
        meeting_config__type=meeting_type
    ).values_list('participants', flat=True)
    # Updating the set with meeting_user_ids.
    user_ids.update(meeting_user_ids)

    return user_services.get_users_for_ids(list(user_ids))
