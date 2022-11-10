from django.utils import timezone

from conversations import models as conversation_models
from conversations.group_helpers import models


def run(dry_run=True):

    groups = conversation_models.Group.objects.filter(
        start__gte=timezone.now()
    )
    print(groups.count())
    for group in groups:
        if not dry_run:
            models.Viewer.objects.create(group=group)
