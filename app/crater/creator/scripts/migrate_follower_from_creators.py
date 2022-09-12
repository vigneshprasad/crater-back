from conversations import models as conversation_models
from crater.creator import models, private, signals


def run(from_creator, to_creator, dry_run=True):

    groups = conversation_models.Group.objects.filter(host=from_creator.user)
    print("Groups to be migrated: {}".format(groups.count()))

    if not dry_run:
        groups.update(host=to_creator.user)
        print("Migrated groups to: {}".format(from_creator.user))

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
