import datetime
import pytz

from django.conf import settings

from resources.meetings import models


def run(dry_run=False):
    meeting_without_start_end = models.Meeting.objects.filter(
        start__isnull=True,
        end__isnull=True
    )
    print(meeting_without_start_end.count())
    for meeting in meeting_without_start_end:
        if not meeting.time_slot:
            print("{} doesn't have time slot".format(meeting.id))
        start = datetime.datetime.combine(
            date=meeting.time_slot.date,
            time=meeting.time_slot.start_time,
            tzinfo=pytz.timezone(settings.TIME_ZONE)
        )
        end = datetime.datetime.combine(
            date=meeting.time_slot.date,
            time=meeting.time_slot.end_time,
            tzinfo=pytz.timezone(settings.TIME_ZONE)
        )
        print("{} time: {} - {}".format(meeting.id, start, end))

        if not dry_run:
            meeting.start = start
            meeting.end = end
            meeting.save()
