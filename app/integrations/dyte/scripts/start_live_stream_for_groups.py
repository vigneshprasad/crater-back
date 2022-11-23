from conversations import models as conversation_models
from integrations.dyte.service import dyte_service_v2


def run(group_ids=None, dry_run=True):
    """Create live stream for group ids."""
    if not group_ids:
        return

    groups = conversation_models.Group.objects.filter(id__in=group_ids)
    for group in groups:
        print("Starting livestream for: {}".format(group.id))
        if not dry_run:
            dyte_meeting = group.dyte_meeting
            livestream = dyte_service_v2.start_livestream_for_meeting(dyte_meeting)
            print("Started livestream: {}".format(livestream))
        print("-----------")


# Update these ids.
ids = []

# run(group_ids=ids)
run(group_ids=ids, dry_run=False)
