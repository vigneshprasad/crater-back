from django.db.models import CharField, Count, Value
from django.db.models.functions import Concat

from conversations import models


def run(dry_run=True):

    duplicate_ids = []
    group_user_list = []

    for group_upvote in models.GroupUpvote.objects.all():
        if (group_upvote.user, group_upvote.group) in group_user_list:
            duplicate_ids.append(group_upvote.id)
            continue
        group_user_list.append((group_upvote.user, group_upvote.group))

    print("Deleting duplicated ids: {}".format(duplicate_ids))

    if not dry_run:
        groups_upvotes_to_delete = models.GroupUpvote.objects.filter(id__in=duplicate_ids)
        groups_upvotes_to_delete.delete(soft=False)
