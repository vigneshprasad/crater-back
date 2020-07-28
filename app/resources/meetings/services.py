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
        stat_date,
        end_date,
        title=choices.DEFAULT_MEETING_TITLE,
        time_slots=None
    ):
    if not time_slots:
        return

    meeting = models.Meeting.objects.create(
        week_start_date=stat_date,
        week_end_date=end_date,
        title=title
    )
    meeting.time_slots.add(time_slots)


def create_default_time_slots(start_date, end_date):

    all_time_slots = []
    date = start_date

    while date < end_date:

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
    slots = []

    for time_slot in time_slots:
        slot = models.TimeSlot.objects.create(
                date=date,
                start_time=time_slot['start_time'],
                end_time=time_slot['end_time']
        )
        slots.append(slot)

    return slots


def get_old_active_meetings():
    return models.Meeting.objects.filter(
        is_closed=False,
        week_end_date__lt=timezone.now().date()
    )
