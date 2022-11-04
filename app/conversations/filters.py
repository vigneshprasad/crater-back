import datetime

from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, IntegerField, Count
from django_filters import rest_framework as filters

from conversations import models, constants


class AllWebinarsFilters(filters.FilterSet):

    start__gte = filters.DateTimeFilter(
        field_name="start",
        lookup_expr="gte",
    )
    sort_by = filters.CharFilter(
        method="custom_sort_by"
    )
    sort_by_category = filters.CharFilter(
        method="custom_category_sort"
    )
    category = filters.CharFilter(
        field_name="categories__slug",
        lookup_expr="exact"
    )

    class Meta:
        model = models.Group
        fields = (
            "host",
            "categories",
            "start__gte",
            "sort_by",
            "sort_by_category",
            "category",
        )

    @staticmethod
    def custom_sort_by(queryset, name, value):
        today = datetime.datetime.now().date()

        if value == constants.SORT_BY_TODAY:
            return queryset.filter(
                start__date=today
            ).order_by("start")

        if value == constants.SORT_BY_THIS_WEEK:
            year, week, _ = today.isocalendar()
            return queryset.filter(
                start__date__year=year,
                start__date__week=week
            ).order_by("start")

        if value == constants.SORT_BY_NEXT_WEEK:
            year, week, _ = (today + datetime.timedelta(weeks=1)).isocalendar()
            return queryset.filter(
                start__date__year=year,
                start__date__week=week
            ).order_by("start")

        if value == constants.SORT_BY_THIS_MONTH:
            return queryset.filter(
                start__date__year=today.year,
                start__date__month=today.month
            ).order_by("start")

        return queryset

    @staticmethod
    def custom_category_sort(queryset, name, value):
        """Return streams sorted by given categories."""

        categories = value.split(",")

        return queryset.annotate(
            relevancy=Count(Case(
                When(
                    categories__slug__in=categories,
                    then=1
                ),
                default=0
            ), distinct=True)
        ).order_by("-is_live", "-relevancy")


class StreamsFollowedFilter(filters.FilterSet):
    hosts = filters.CharFilter(
        method="custom_host_filter"
    )

    class Meta:
        model = models.Group
        fields = (
            "host",
            "hosts",
            "categories"
        )

    @staticmethod
    def custom_host_filter(queryset, name, value):
        host_ids = value.split(",")
        return queryset.filter(
            host_id__in=host_ids
        )
