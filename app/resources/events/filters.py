from django_filters import rest_framework as filters

from resources.events.models import Event


class EventFilter(filters.FilterSet):
    participants = filters.BooleanFilter(method='filter_participants')

    class Meta:
        model = Event
        fields = ['participants', 'is_free', 'state']

    def filter_participants(self, queryset, name, value):
        if value:
            return queryset.filter(participants__user=self.request.user, state='upcoming')
        return queryset
