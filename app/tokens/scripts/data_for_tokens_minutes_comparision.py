from django.db.models import *

from conversations.models import *
from integrations.dyte.models import *
from tokens.models import *
from users.models import *

token_start_date = "2022-07-27"

learn_streams = Group.objects.filter(
    host__creator__tokens_enabled=True,
    start__gte=token_start_date,
    is_published=True,
    closed=True
)

messages = GroupMessage.objects.filter(
    group__in=learn_streams
)

dyte_meeting_participants = DyteMeetingParticipant.objects.filter(
    dyte_meeting__group__in=learn_streams,
    last_online_at__isnull=False
)

# Will give users who have watch 1+ learn streams.
users_who_watch_learn_streams = dyte_meeting_participants.values("participant_id").annotate(
    participant_count=Count("participant_id")
).filter(participant_count__gte=10)

users = [User.objects.get(pk=a["participant_id"]) for a in users_who_watch_learn_streams]

for user in users:

    if user.is_creator:
        continue

    total_time_spent = 0
    total_time_spent_minutes = 0
    participants = dyte_meeting_participants.filter(participant=user)

    for participant in participants:
        total_time_spent += participant.total_minutes_watched
        total_time_spent_minutes += participant.minutes_spent

    interactions = messages.filter(sender=user).count()

    learn_earned = total_time_spent + (2 * interactions)
    learn_earned_2 = total_time_spent_minutes + (2 * interactions)
    learn_earned_3 = UserTokenLog.objects.filter(
        user=user,
        type=1,
        date__gte=token_start_date
    ).aggregate(total_amount=Sum("amount"))["total_amount"] or 0

    total_minutes_minus_logs = learn_earned - learn_earned_3
    minutes_spent_minus_logs = learn_earned_2 - learn_earned_3

    print(user)
    print("Diff between total_minutes_watched calculation: {}".format(total_minutes_minus_logs))
    print("Diff between minutes_spent calculation: {}".format(minutes_spent_minus_logs))
    print("total_minutes_watched: ", learn_earned)
    print("minutes_spent: ", learn_earned_2)
    print("user_token_log: ", learn_earned_3)
    print("-" * 30)
