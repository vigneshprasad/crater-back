from django.utils import timezone

from integrations.dyte import models


def run(dry_run=True):
    now = timezone.now()
    yesterday = now - timezone.timedelta(days=1)
    online_dyte_participants = models.DyteMeetingParticipant.objects.filter(
        is_online=True,
        dyte_meeting__group__start__lte=yesterday
    )

    print(online_dyte_participants.count())

    for dyte_participant in online_dyte_participants:
        print(dyte_participant)
        group = dyte_participant.dyte_meeting.group
        print(group)
        print(group.local_start)
        online_logs = dyte_participant.online_logs.all()
        online_online_logs = online_logs.filter(is_offline=False)
        print(online_online_logs)
        if online_online_logs:
            print(group.last_live_at)
            if not dry_run:
                for log in online_online_logs:
                    log.offline_at = group.last_live_at
                    log.is_offline = True
                    log.save()

                dyte_participant.last_online_at = group.last_live_at
                dyte_participant.is_online = False
                dyte_participant.save()
        else:
            online_log = online_logs.last()
            print(online_log.offline_at)
            if not dry_run:
                dyte_participant.last_online_at = online_log.offline_at
                dyte_participant.is_online = False
                dyte_participant.save()

        print("-"*30)
