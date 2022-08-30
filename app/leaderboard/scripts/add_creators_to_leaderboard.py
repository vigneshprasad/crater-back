from django.contrib.auth import get_user_model
from django.db.models import Sum

from conversations import models as conversation_models
from leaderboard import models, tasks


def run(leaderboard_id, max_users=5, start_date=None, end_date=None, dry_run=True):

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
    leaderboard_participants_dict = {}

    print("Creators with 2+ streams in the duration.")
    for host in hosts:
        host_groups = groups.filter(host=host)
        group_count = host_groups.count()
        minutes_watched = host_groups.aggregate(
            minutes=Sum("total_minutes_spent_by_attendees")
        )["minutes"] or 0

        # If the creator hasn't streamed minimum of two times, don't
        # add the creator to the leaderboard.
        if group_count < 2:
            continue

        # If the creators watch time is less than 1000, don't add creator
        # to the leaderboard.
        if minutes_watched < 1000:
            continue

        # Append the user and minutes to a dict with
        # user.pk as key and minutes as value.
        user = get_user_model().objects.get(pk=host)
        if leaderboard_participants_dict.get(user.pk):
            leaderboard_participants_dict[user.pk] += minutes_watched
        else:
            leaderboard_participants_dict[user.pk] = minutes_watched

    # Reverse sort the dict of user and minutes
    leaderboard_participants_sorted_dict = dict(sorted(
        leaderboard_participants_dict.items(),
        key=lambda item: item[1],
        reverse=True
    ))

    for user_pk, minutes in leaderboard_participants_sorted_dict.items():
        user = get_user_model().objects.get(pk=user_pk)
        if len(leaderboard_participants) < max_users:
            print(user)
            print(groups.filter(host=user).count())
            print(minutes)
            print("-" * 30)
            leaderboard_participants.append(user)

    print("Adding {} participants to Leaderboard: {}".format(len(leaderboard_participants), leaderboard))

    if not dry_run:
        leaderboard.participants.add(*leaderboard_participants)
        print("Added all participants")
        print("Recalculating leaderboard")
        tasks.recalculate_leaderboards([leaderboard.id])
        print("Recalculation done")
