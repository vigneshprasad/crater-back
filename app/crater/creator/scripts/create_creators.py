from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import models as crater_models


def run(dry_run=True):
    webinars = conversation_models.Group.objects.filter(type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM)
    for webinar in webinars:
        print("Start", "*" * 10)
        print("Webinar: {}".format(webinar))

        host = webinar.host
        if not host:
            print("Group has no host")

        creator = crater_models.Creator.objects.filter(user=host)
        if creator.exists():
            print("Creator already exists")
            continue
        
        print("Making Creator Object {}".format(host.email))

        if not dry_run:
            creator = crater_models.Creator.objects.create(
                user=host,
                subscriber_count=1000,
                certified=False,
                order=0,
            )
            creator.save()

        print("End", "*" * 10)
