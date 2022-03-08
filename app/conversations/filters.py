from django_filters import rest_framework as filters

from conversations import models


class AllWebinarsFilters(filters.FilterSet):

    start__gte = filters.DateTimeFilter(
        field_name="start",
        lookup_expr="gte",
    )

    class Meta:
        model = models.Group
        fields = (
            "host",
            "categories",
            "start__gte"
        )
