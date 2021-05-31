import datetime
import pytz

from django.db.models import Q

from resources.meetings import models


def run(dry_run=True):
    # Get all time slot with missing start and end.
    time_slots = models.TimeSlot.objects.filter(
        Q(start__isnull=True) | Q(end__isnull=True),
    )
    for time_slot in time_slots:
        print("Start", "*"*30)
        # Note: start time and end time are in local time.
        # Create start and end in UTC for time slot.
        start = datetime.datetime.combine(time_slot.date, time_slot.start_time).astimezone(tz=pytz.utc)
        end = datetime.datetime.combine(time_slot.date, time_slot.end_time).astimezone(tz=pytz.utc)

        print("Updating Time Slot: {}".format(time_slot.id))
        print("Time Slot Date: {}".format(time_slot.date))
        print("Time Slot Start Time: {}".format(time_slot.start_time))
        print("Time Slot End Time: {}".format(time_slot.end_time))
        # Updated start and end.
        print("Time Slot Start: {}".format(start))
        print("Time Slot End: {}".format(end))

        if not dry_run:
            time_slot.start = start
            time_slot.end = end
            time_slot.save()

        print("End", "*"*30)
