import datetime

from conversations import models, constants
from integrations.dyte import models as dyte_models


def run(dry_run=True):
    """Change group last_live_at to actual time the host ends the meeting."""
    start_date = dyte_models.DyteMeetingParticipant.objects.first().created_at.date()
    end_date = datetime.date.today()
    groups = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=start_date,
        start__lte=end_date,
        closed=True
    )

    for group in groups:
        host_dyte_participant = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not host_dyte_participant:
            continue
        print(host_dyte_participant.last_online_at)
        print(group.last_live_at)

        if not dry_run:
            group.last_live_at = host_dyte_participant.last_online_at
            group.save()
            print("Updated last live at for group.")
            print(group.last_live_at)

        print("---------")
