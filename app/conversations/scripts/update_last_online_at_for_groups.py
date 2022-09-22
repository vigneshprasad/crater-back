import datetime

import pytz
from django.conf import settings

from conversations import models, constants
from integrations.dyte import models as dyte_models


def run(groups=None, dry_run=True):
    """Change group last_live_at to actual time the host ends the meeting."""

    start_date = dyte_models.DyteMeetingParticipant.objects.first().created_at.date()
    end_date = datetime.date.today()
    groups = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=start_date,
        start__lte=end_date,
        closed=True
    ) if not groups else groups

    for group in groups:
        print("----------------------")
        print(group.id)
        print(group.get_display_start())
        host_dyte_participant = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not host_dyte_participant:
            continue

        group_last_live_at = group.last_live_at
        host_participant_last_online_at = host_dyte_participant.last_online_at
        host_online_log = host_dyte_participant.online_logs.last()
        host_online_log_offline_time = host_online_log.offline_at if host_online_log else None
        if not host_online_log_offline_time:
            continue

        print(host_participant_last_online_at.astimezone(
            pytz.timezone(settings.TIME_ZONE)
        ).strftime("%A, %d %B %I:%M %p") if host_participant_last_online_at else None)

        print(group_last_live_at.astimezone(
                pytz.timezone(settings.TIME_ZONE)
            ).strftime("%A, %d %B %I:%M %p") if group_last_live_at else None)

        print(host_online_log_offline_time.astimezone(
                pytz.timezone(settings.TIME_ZONE)
            ).strftime("%A, %d %B %I:%M %p") if host_online_log_offline_time else None)

        if host_participant_last_online_at and group_last_live_at:
            min_time = min(host_participant_last_online_at, group_last_live_at)
        else:
            min_time = None

        if min_time and host_online_log_offline_time:
            last_live_at_time = min(min_time, host_online_log_offline_time)
        else:
            last_live_at_time = min_time

        print(last_live_at_time.astimezone(
                pytz.timezone(settings.TIME_ZONE)
            ).strftime("%A, %d %B %I:%M %p") if last_live_at_time else None)

        if not dry_run:
            host_dyte_participant.last_online_at = last_live_at_time
            host_dyte_participant.save()
            print("Updated host participant last_online_at")
            group.last_live_at = last_live_at_time
            group.save()
            print("Updated last live at for group.")
