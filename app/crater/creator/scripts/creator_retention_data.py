import datetime

from crater.creator import models
from conversations import constants as conversation_constants
from conversations import models as conversation_models

YEAR = 2021


def _generate_start_date_for_months(year):
    return {
        "jan": datetime.datetime(year, 1, 1),
        "feb": datetime.datetime(year, 2, 1),
        "march": datetime.datetime(year, 3, 1),
        "april": datetime.datetime(year, 4, 1),
        "may": datetime.datetime(year, 5, 1),
        "june": datetime.datetime(year, 6, 1),
        "july": datetime.datetime(year, 7, 1),
        "aug": datetime.datetime(year, 8, 1),
        "sept": datetime.datetime(year, 9, 1),
        "oct": datetime.datetime(year, 10, 1),
        "nov": datetime.datetime(year, 11, 1),
        "dec": datetime.datetime(year, 12, 1),
        "jan_next": datetime.datetime(year + 1, 1, 1)
    }


def get_data(year=None, monthly=False, combined=False):

    year = year if year else YEAR
    global month_start_dates
    month_start_dates = _generate_start_date_for_months(year)

    if combined:
        get_all_data_split_by_month()

    if monthly:
        print("*"*30)
        get_data_based_on_start_and_end(month_start_dates.get("sept"), month_start_dates.get("oct"))
        print("*" * 30)
        get_data_based_on_start_and_end(month_start_dates.get("oct"), month_start_dates.get("nov"))
        print("*" * 30)
        get_data_based_on_start_and_end(month_start_dates.get("nov"), month_start_dates.get("dec"))
        print("*"*30)


def get_data_based_on_start_and_end(start_date, end_date):

    creators = models.Creator.objects.all()
    creator_user_ids = creators.values_list("user", flat=True)
    webinars = conversation_models.Group.objects.filter(
        start__gte=start_date,
        end__lt=end_date,
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for host_id in creator_user_ids:
        creator_webinars = webinars.filter(host=host_id).order_by("start")
        if not creator_webinars:
            continue

        # Get total and unique rsvps.
        rsvps = conversation_models.Request.objects.filter(
            group__in=creator_webinars
        )
        unique_rsvps = rsvps.distinct("requester")

        # Get first and last session of the creator.
        first_session = creator_webinars.first()
        last_session = creator_webinars.last()

        # Get creator user object.
        creator = creators.get(user_id=host_id)
        creator_user = creator.user

        print(
            creator_user.display_name, ",",
            creator_webinars.count(), ",",
            rsvps.count(), ",",
            unique_rsvps.count(), ",",
            first_session.local_start.date(), ",",
            last_session.local_end.date()
        )


def get_all_data_split_by_month():

    creators = models.Creator.objects.all()
    creator_user_ids = creators.values_list("user", flat=True)
    webinars = conversation_models.Group.objects.filter(
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
        start__lte=datetime.datetime.now()
    )

    for host_id in creator_user_ids:
        creator_webinars = webinars.filter(host=host_id).order_by("start")
        if not creator_webinars:
            continue

        # Get total and unique rsvps.
        rsvps = conversation_models.Request.objects.filter(
            group__in=creator_webinars
        )
        unique_rsvps = rsvps.distinct("requester")

        # Monthly split of webinars.
        september_webinars = creator_webinars.filter(
            start__gte=month_start_dates.get("sept"),
            end__lt=month_start_dates.get("oct")
        )
        october_webinars = creator_webinars.filter(
            start__gte=month_start_dates.get("oct"),
            end__lt=month_start_dates.get("nov")
        )
        november_webinars = creator_webinars.filter(
            start__gte=month_start_dates.get("nov"),
            end__lt=month_start_dates.get("dec")
        )

        # Get first and last session of the creator.
        first_session = creator_webinars.first()
        last_session = creator_webinars.last()

        # Get creator user object.
        creator = creators.get(user_id=host_id)
        creator_user = creator.user

        print(
            creator_user.display_name, ",",
            september_webinars.count(), ",",
            october_webinars.count(), ",",
            november_webinars.count(), ",",
            rsvps.count(), ",",
            unique_rsvps.count(), ",",
            first_session.local_start.date(), ",",
            last_session.local_end.date()
        )
