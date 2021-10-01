from conversations import models as conversation_models
from conversations import constants as conversation_constants
from conversations import signals as conversation_signals


def run(dry_run=True):

    all_requests = conversation_models.Request.objects.filter(
        participant_type=conversation_constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
    )

    for request in all_requests:
        if not dry_run:
            # Will creator followers for creators and add the user to
            # community of the creator.
            conversation_signals.attendee_added_to_group.send(
                sender=request.__dict__,
                user=request.requester,
                group=request.group
            )
