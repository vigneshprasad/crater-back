from django.db.models import Count, Sum

from conversations import models as conversation_models
from integrations.dyte import models as dyte_models
from tokens import models
from tokens.learn import constants as learn_constants
from users import models as user_models

token_start_date = learn_constants.LEARN_TOKEN_START_DATE

learn_streams = conversation_models.Group.objects.filter(
    host__creator__tokens_enabled=True,
    start__gte=token_start_date,
    is_published=True,
    closed=True
)

messages = conversation_models.GroupMessage.objects.filter(
    group__in=learn_streams
)

dyte_meeting_participants = dyte_models.DyteMeetingParticipant.objects.filter(
    dyte_meeting__group__in=learn_streams,
    last_online_at__isnull=False
)

# Will give users who have watch 1+ learn streams.
users_who_watch_learn_streams = dyte_meeting_participants.values("participant_id").annotate(
    participant_count=Count("participant_id")
).filter(participant_count__gte=10)

users = [user_models.User.objects.get(pk=a["participant_id"]) for a in users_who_watch_learn_streams]

for user in users:

    if user.is_creator:
        continue

    total_time_spent = 0
    total_time_spent_minutes = 0
    participants = dyte_meeting_participants.filter(participant=user)

    for participant in participants:
        total_time_spent += participant.total_minutes_watched
        total_time_spent_minutes += participant.time_spent

    interactions = messages.filter(sender=user).count()

    learn_earned = total_time_spent + (2 * interactions)
    learn_earned_2 = total_time_spent_minutes + (2 * interactions)
    learn_earned_3 = models.UserTokenLog.objects.filter(
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
