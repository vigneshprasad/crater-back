from django_filters import rest_framework as filters

from resources.events.models import Event


class EventFilter(filters.FilterSet):
    participated = filters.BooleanFilter(method='filter_participated')
    state = filters.CharFilter(method='filter_states')
    location = filters.CharFilter(method='filter_locations')

    class Meta:
        model = Event
        fields = ['participated', 'is_free', 'state', 'location']

    def filter_participated(self, queryset, name, value):
        if value:
            return queryset.filter(participants__user=self.request.user, state='upcoming')
        return queryset

    @staticmethod
    def filter_states(queryset, name, value):
        if value:
            _filters = value.split(',')
            return queryset.filter(state__in=_filters)
        return queryset

    @staticmethod
    def filter_locations(queryset, name, value):
        if value:
            _filters = value.split(',')
            return queryset.filter(location__in=_filters)
        return queryset
