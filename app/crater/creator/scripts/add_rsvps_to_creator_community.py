from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import private


def run(dry_run=True):

    all_requests = conversation_models.Request.objects.filter(
        participant_type=conversation_constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
    )

    for request in all_requests:

        print("----------")
        user = request.requester
        host = request.group.host
        if not host:
            continue

        creator = private.get_or_create_creator(host)
        follower = private.get_follower_for_user_and_creator_id(user, creator.id)
        if follower:
            print("Follower is already present for {} and {}".format(creator.user.__str__(), user.__str__()))
            continue

        print("User: ", user)
        print("Host: ", host)
        print("Creator ID: ", creator.id)

        if not dry_run:
            print("Adding follower for {} and {}".format(creator.user.__str__(), user.__str__()))
            private.create_follower_for_creator(user, creator)

        print("----------")
