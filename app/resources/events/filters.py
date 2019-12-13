from django_filters import rest_framework as filters

from resources.events.models import Event


class EventFilter(filters.FilterSet):
    rsvpds = filters.BooleanFilter(method='filter_rsvpds')

    class Meta:
        model = Event
        fields = ['rsvpds', 'is_free', 'state']

    def filter_rsvpds(self, queryset, name, value):
        if value:
            return queryset.filter(rsvpds__user=self.request.user, state='upcoming')
        return queryset
