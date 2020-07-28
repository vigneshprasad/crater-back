import datetime

from django.utils import timezone

from tags.serializers import InterestsSerializer
from tags.models import Interests
from resources.meetings import choices
from resources.meetings import models


def get_objectives_list():
    objectives = [{
        'key': objective[0],
        'label': objective[1] 
    } for objective in choices.OBJECTIVE_CHOICES]
    return objectives


def get_interest_list():
    interests = InterestsSerializer(data=Interests.objects.all(), many=True)
    interests.is_valid()
    return interests.data


def create_meetings_for_time_period(
        start_date,
        end_date,
        title=choices.DEFAULT_MEETING_TITLE,
        time_slots=None,
        registration_end_date=None
):
    """
    Creates meeting object for a give time period.

    Args:
        start_date(Date): Meeting start date.
        end_date(Date): Meeting end date.
        title(Char): Meeting title. Not required since
            default is provided.
        time_slots(list(TimeSlot)): List of TimeSlots objects
            for the meeting. If not provided these are created
            with a set of default time slots.
        registration_end_date(Date): Meeting registration closing
            date.

    Returns:
        Created Meeting object.

    """
    if not time_slots:
        time_slots = create_default_time_slots(start_date, end_date)

    # If registration end date is not present, week end
    # is taken as default registration end date.
    if not registration_end_date:
        registration_end_date = end_date

    meeting, _ = models.Meeting.objects.get_or_create(
        week_start_date=start_date,
        week_end_date=end_date,
        registration_end_date=registration_end_date,
        title=title
    )
    # Added time slots to the meeting object.
    meeting.available_time_slots.add(*time_slots)

    return meeting


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


def get_old_active_meetings():
    """
    Closes meetings based on info provided
    in the model. (week_end_date)

    return:
        Queryset of meetings.

    """
    return models.Meeting.objects.filter(
        is_active=True,
        week_end_date__lt=timezone.now().date()
    )


def get_meetings_with_open_registration():
    """
    Closes registration for meeting based on info provided
    in the model. (registration_end_date)

    return:
        Queryset of meetings.

    """
    return models.Meeting.objects.filter(
        is_registration_opne=True,
        registration_end_date__lt=timezone.now().date()
    )
