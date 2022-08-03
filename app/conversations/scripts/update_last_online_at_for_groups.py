from conversations import models, constants
from integrations.dyte import models as dyte_models


def run():

    start_date = dyte_models.DyteMeetingParticipant.objects.first().created_at.date()
    groups = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=start_date
    )

    for group in groups:
        host_dyte_participant = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not host_dyte_participant:
            continue

        group.last_live_at = host_dyte_participant.last_online_at
        group.save()
