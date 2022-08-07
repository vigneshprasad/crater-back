import datetime

from django_filters import rest_framework as filters

from conversations import models


class AllWebinarsFilters(filters.FilterSet):

    start__gte = filters.DateTimeFilter(
        field_name="start",
        lookup_expr="gte",
    )
    sort_by = filters.CharFilter(
        method="custom_sort_by"
    )

    class Meta:
        model = models.Group
        fields = (
            "host",
            "categories",
            "start__gte",
            "sort_by",
        )

    def custom_sort_by(self, queryset, name, value):
        today = datetime.datetime.now().date()

        if value == "today":
            return queryset.filter(
                start__date=today
            ).order_by("start")

        if value == "this_week":
            year, week, _ = today.isocalendar()
            return queryset.filter(
                start__date__year=year,
                start__date__week=week
            ).order_by("start")

        if value == "next_week":
            year, week, _ = (today + datetime.timedelta(weeks=1)).isocalendar()
            return queryset.filter(
                start__date__year=year,
                start__date__week=week
            ).order_by("start")

        if value == "this_month":
            return queryset.filter(
                start__date__year=today.year,
                start__date__month=today.month
            ).order_by("start")

        if value == "recently_added":
            return queryset.order_by("-created_at")

        return queryset
