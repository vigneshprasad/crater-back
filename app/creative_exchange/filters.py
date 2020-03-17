from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as filters

from creative_exchange.models import ExchangeRequest


class BuyerFilter(SimpleListFilter):
    title = _('Buyer')
    parameter_name = 'buyer'

    def lookups(self, request, model_admin):
        buyers = ExchangeRequest.objects.values('user', 'user__name').distinct()
        return [(buyer['user'], buyer['user__name']) for buyer in buyers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user=self.value())
        return queryset


class RequestFilter(filters.FilterSet):
    days_from = filters.NumberFilter(field_name='days', lookup_expr='gte')
    days_to = filters.NumberFilter(field_name='days', lookup_expr='lte')
    budget_from = filters.NumberFilter(field_name='extended_price', lookup_expr='gte')
    budget_to = filters.NumberFilter(field_name='extended_price', lookup_expr='lte')

    class Meta:
        model = ExchangeRequest
        fields = [
            'days_from',
            'days_to',
            'category',
            'extended_price',
            'user__city',
            'budget_from',
            'budget_to',
            'city'
        ]

