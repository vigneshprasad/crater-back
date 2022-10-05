from conversations import models as conversation_models
from crater.creator import models, private, signals
from integrations.dyte import models as dyte_models


def run(from_creator, to_creator, dry_run=True):
    """Migrate followers and streams from one creator to the other.

    Note:
        This is used when 2 different objects are created for the
            same user.

    """
    from_user = from_creator.user
    to_user = to_creator.user

    groups = conversation_models.Group.objects.filter(host=from_user)
    # We are migrating a host dyte participants so that the max minutes (host minutes
    # spent) on the stream does not change if we change the host.
    dyte_participants_for_host = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group__in=groups,
        participant=from_user
    )
    print("Groups to be migrated: {}".format(groups.count()))
    print("Dyte participants to be migrated: {}".format(dyte_participants_for_host.count()))

    if not dry_run:
        groups.update(host=to_user)
        dyte_participants_for_host.update(participant=to_user)
        print("Migrated groups to: {}".format(to_user))
        print("Migrated dyte participants for host to: {}".format(to_user))

    from_followers = models.Follower.all_objects.filter(creator=from_creator)

    for follower in from_followers:
        print("--------")
        f = private.get_follower_for_user_and_creator_id(follower.user, to_creator.id)
        user = follower.user

        if f:
            print("Follower is already present for {} and {}".format(
                to_creator.id, user.__str__())
            )
            continue

        print("User: ", user)
        print("Creator ID: ", to_creator.id)

        if not dry_run:
            print("Adding follower for {} and {}".format(to_creator.id, user.__str__()))
            follower.creator = to_creator
            follower.save()
            signals.creator_followed.send(
                sender=follower.__class__,
                follower=follower
            )

        print("----------")
