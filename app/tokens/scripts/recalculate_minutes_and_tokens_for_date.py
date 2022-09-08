from conversations import models as conversation_models
from integrations.dyte import tasks as dyte_tasks
from tokens import tasks


def run(date, dry_run=True):

    group_ids_for_the_date = conversation_models.Group.objects.filter(
        start__gte=date,
        start__lte=date
    ).values_list("id", flat=True)

    print("Recalculating minutes for {} groups".format(len(group_ids_for_the_date)))
    print(group_ids_for_the_date)
    if not dry_run:
        dyte_tasks.recalculate_minutes_for_groups(group_ids=group_ids_for_the_date)
        print("Recalculated minutes")

    print("Updating tokens for date: {}".format(date))
    if not dry_run:
        tasks.calculate_tokens_earned(date)
        print("Updated tokens")

    print("--------")
