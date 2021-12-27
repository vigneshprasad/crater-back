from django.db.models import Count, Max
from integrations.dyte.models import *

unique_fields = ["dyte_meeting", "participant"]


def run(dry_run=True):

    duplicates = (
        DyteMeetingParticipant.objects.values(*unique_fields)
        .order_by()
        .annotate(max_id=Max("id"), count_id=Count("id"))
        .filter(count_id__gt=1)
    )

    for duplicate in duplicates:
        print(duplicate)

        duplicate_dyte_meeting_participants = DyteMeetingParticipant.objects.filter(
            **{x: duplicate[x] for x in unique_fields}
        ).exclude(id=duplicate["max_id"])

        print("Deleting: ")
        print(duplicate_dyte_meeting_participants)
        if dry_run:
            continue

        duplicate_dyte_meeting_participants.delete(soft=False)
        print("Deleted")
