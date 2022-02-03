from conversations import constants
from conversations import models
from conversations import services
from integrations.dyte import models as dyte_models
from crater.creator import receivers


EMAIL_TO_EXCLUDE = [
    "vignesh@worknetwork.in",
    "abhishek@worknetwork.in",
    "nishant@worknetwork.in",
    "vivan@crater.club",
    "vivan@worknetwork.in",
    "ram@worknetwork.in",
    "sujith@crater.club",
    "shivanivijay2796@gmail.com",
    "shivaniv27@yahoo.co.in",
    "rjtnndn@gmail.com",
    "sanjeevraichur29@gmail.com"
]


def run(dry_run=True):

    dyte_participants = dyte_models.DyteMeetingParticipant.objects.filter(
        updated_at__gte="2022-01-17",
        updated_at__lte="2022-01-18",
        last_online_at__isnull=False
    ).exclude(
        participant__email__in=EMAIL_TO_EXCLUDE
    ).order_by("updated_at")

    for participant in dyte_participants:

        user = participant.participant
        group = participant.dyte_meeting.group

        if not (group and group.type == constants.GROUP_TYPE_WEBINAR_ENUM):
            continue

        if user in group.get_host_and_speakers():
            continue

        request = services.get_request_for_user_and_group_id(
            user,
            group
        )
        if request:
            continue

        print(group.id, participant.last_online_at, group.start, user)

        if not dry_run:
            # Create request.
            request = models.Request.objects.create(
                requester=user,
                group=group,
                status=constants.REQUEST_STATUS_ACCEPTED_ENUM,
                participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
            )

            # Add to group attendees.
            group.attendees.add(user)

            # Add attendee to creator followers.
            receivers.add_attendee_to_creator_followers(
                sender=request.__class__,
                group=request.group,
                user=user
            )
