from crater.creator import models
from crater.creator import private


def run(dry_run=True):
    creators = models.Creator.objects.all()
    for creator in creators:
        print("Creator: ", creator.user.__str__())
        subscriber_count = private.get_subscriber_count_for_creator(creator)
        print("Subscribers: ", subscriber_count)

        if not dry_run:
            creator.subscriber_count = subscriber_count
            creator.save()
            print("Updated Subscriber count for {}".format(creator.user.__str__()))
