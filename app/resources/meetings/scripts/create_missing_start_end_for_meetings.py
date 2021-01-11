import datetime

from resources.meetings import models


def run(dry_run=True):
    meeting_without_start_end = models.Meeting.objects.filter(
        start__isnull=True,
        end__isnull=True
    )
    print(meeting_without_start_end.count())

    for meeting in meeting_without_start_end:
        print("-"*30)
        if not meeting.time_slot:
            print("{} doesn't have time slot".format(meeting.id))
            continue

        start = datetime.datetime.combine(
            date=meeting.time_slot.date,
            time=meeting.time_slot.start_time
        )
        end = datetime.datetime.combine(
            date=meeting.time_slot.date,
            time=meeting.time_slot.end_time
        )

        print("Start and end for meeting {}: {} - {}".format(meeting.id, start, end))
        print("-"*30)

        if not dry_run:
            meeting.start = start
            meeting.end = end
            meeting.save()
