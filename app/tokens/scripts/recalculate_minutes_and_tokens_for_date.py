import datetime

import pytz
from django.conf import settings

from conversations import models as conversation_models
from integrations.dyte import tasks as dyte_tasks
from tokens import tasks


def recalculate_minutes_for_groups(date, dry_run=True):

    today = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    today_start = datetime.datetime.combine(today, datetime.time())
    today_end = datetime.datetime.combine(today, datetime.time(23, 59))
    # Make datetime timezone aware.
    timezone = pytz.timezone(settings.TIME_ZONE)
    today_start = timezone.localize(today_start)
    today_end = timezone.localize(today_end)
    print(today_start, today_end)

    # Only get streams whose hosts are eligible for learn tokens.
    streams_for_date = conversation_models.Group.objects.filter(
        start__gte=today_start,
        start__lte=today_end
    ).values_list("id", flat=True)

    print("Recalculating minutes for {} groups".format(len(streams_for_date)))
    print(streams_for_date)
    if not dry_run:
        dyte_tasks.recalculate_minutes_for_groups(group_ids=streams_for_date)
        print("Recalculated minutes")

    print("*"*30)


def recalculate_tokens_for_date(date, dry_run=True):

    print(date)
    print("Updating tokens for date: {}".format(date))
    if not dry_run:
        tasks.calculate_tokens_earned(date)
        print("Updated tokens")

    print("-"*30)
