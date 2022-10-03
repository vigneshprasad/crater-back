import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from conversations import models
from integrations.dyte.service import dyte_service

DEFAULT_START_FOR_DYTE = datetime.datetime(2022, 1, 1)


def get_per_user_data_from_dyte(start_date=None, end_date=None):
    """Get per user data (minutes watched) from dyte."""
    start_datetime = None
    end_datetime = None

    if not start_date:
        start_date = DEFAULT_START_FOR_DYTE
        start_datetime = start_date.date()

    if not end_date:
        end_date = timezone.now()
        end_datetime = end_date.date()

    start_datetime = start_datetime if start_datetime else datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_datetime = end_datetime if end_datetime else datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    start = start_datetime if start_datetime > DEFAULT_START_FOR_DYTE.date() else DEFAULT_START_FOR_DYTE.date()

    groups = models.Group.objects.filter(
        start__gte=start,
        start__lte=end_datetime
    )

    webinar_data_from_dyte = dyte_service.get_stats_for_meetings(groups)
    user_pks = list(map(lambda d: d["clientSpecificId"], webinar_data_from_dyte))
    unique_user_pks = list(set(user_pks))

    final_data = []
    for user_pk in unique_user_pks:
        user_data = list(filter(lambda item: item["clientSpecificId"] == user_pk, webinar_data_from_dyte))
        merged_user_data = {
            "clientSpecificId": user_pk,
            "numberOfSessions": len(user_data),
            "totalMinutes": 0
        }
        for i in user_data:
            merged_user_data["totalMinutes"] += i["totalMinutes"]
        final_data.append(merged_user_data)

    for j in final_data:
        user = get_user_model().objects.get(pk=j["clientSpecificId"])
        print(
            user.email, "#",
            user.__str__(), "#",
            j["numberOfSessions"], "#",
            j["totalMinutes"], "#",
        )
    return final_data
