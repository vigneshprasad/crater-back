from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import private
from crater.creator import signals


def run(dry_run=True):

    all_requests = conversation_models.Request.objects.filter(
        participant_type=conversation_constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
    )

    for request in all_requests:
        if not dry_run:
            # Will creator followers for creators and add the user to
            # community of the creator.
            host = request.group.host
            if not host:
                continue

            creator = private.get_or_create_creator(host)
            follower = private.create_follower_for_creator(request.requester, creator)

            # Send signal so user get added to community and all.
            signals.creator_followed.send(
                sender=follower.__class__,
                follower=follower
            )
