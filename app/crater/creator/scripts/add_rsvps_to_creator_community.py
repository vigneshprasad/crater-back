from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import models
from crater.creator import private


def run(dry_run=True):

    all_requests = conversation_models.Request.objects.filter(
        participant_type=conversation_constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
    )

    for request in all_requests:

        if not dry_run:
            # Will creator followers for creators and add the user to
            # community of the creator.
            host = request.host
            try:
                creator = host.creator
            except models.Creator.DoesNotExist:
                continue

            private.create_follower_for_creator(request.requester, creator)
            default_community = private.get_default_community_for_creator(creator)
            private.add_user_to_community(request.requester, default_community)
