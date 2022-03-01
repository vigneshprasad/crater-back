from conversations import constants
from conversations import models
from crater.creator import models as creator_models


def run(group_id, dry_run=True):

    group = models.Group.objects.get(id=group_id)
    rsvps = models.Request.objects.filter(
        group_id=group_id,
        participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
    )
    host = group.host
    host_profile = host.profile

    if not host_profile.is_creator:
        print("{} is not a creator.".format(host.name))

    total_followers_added = 0
    total_followers_to_add = 0

    for rsvp in rsvps:

        print("-------")
        user = rsvp.requester
        follower = creator_models.Follower.objects.filter(
            creator__user=host,
            user=user
        )

        if follower:
            continue

        print("Host: {}".format(host))
        print("User: {}".format(user))
        total_followers_to_add += 1
        if not dry_run:
            print("Creating follower")
            follower = creator_models.Follower.objects.create(
                creator=host.creator,
                user=user
            )
            total_followers_added += 1
            print("Created follower: {}".format(follower.id))

        print("------")

    return total_followers_to_add, total_followers_added
