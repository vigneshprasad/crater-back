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


def run_with_concat(dry_run=True):
    concat_group_upvotes = models.GroupUpvote.objects.annotate(
        unique_str=Concat("user_id", Value(" "), "group_id", output_field=CharField())
    )
    concat_count_group_upvotes = concat_group_upvotes.values("id", "unique_str").annotate(unique_str_count=Count("unique_str"))
    duplicates = concat_count_group_upvotes.filter(full_name_count__gt=1)
    print(duplicates)


def run_with_count(dry_run=True):
    duplicates = models.GroupUpvote.objects.values(
        "id",
        "user",
        "group"
    ).annotate(
        user_count=Count("user"),
        group_count=Count("group")
    ).filter(
        user_count__gt=1, group_count__gt=1
    )
    print(duplicates)
