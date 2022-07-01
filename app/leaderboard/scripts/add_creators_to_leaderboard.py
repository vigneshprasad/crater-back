import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum

from conversations import models as conversation_models
from leaderboard import models, tasks


def run(leaderboard_id, start_date=None, end_date=None, dry_run=True):

    leaderboard = models.Leaderboard.objects.get(id=leaderboard_id)
    if not end_date:
        end_date = leaderboard.end
        start_date = leaderboard.start

    print(start_date.date(), end_date.date())

    groups = conversation_models.Group.objects.filter(
        start__gte=start_date,
        end__lte=end_date
    )

    hosts = groups.values_list("host", flat=True)
    hosts = list(set(hosts))

    print("Adding creators to leaderboard: {}".format(leaderboard))
    leaderboard_participants = []

    print("Creators with 2+ streams in the duration.")
    for host in hosts:
        host_groups = groups.filter(host=host)
        group_count = host_groups.count()
        minutes_watched = host_groups.aggregate(minutes=Sum("total_minutes_spent_by_attendees"))["minutes"] or 0
        # if group_count < 2:
        #     continue
        if minutes_watched < 1000:
            continue

        user = get_user_model().objects.get(pk=host)
        print(user)
        print(group_count)
        print(minutes_watched)
        print("-"*30)
        leaderboard_participants.append(user)

    print("Adding {} participants to Leaderboard: {}".format(len(leaderboard_participants), leaderboard))
    if not dry_run:
        leaderboard.participants.add(*leaderboard_participants)
        print("Added all participants")
        print("Recalculating leaderboard")
        tasks.recalculate_leaderboards(leaderboard.id)
        print("Recalculation done")
