from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from creative_exchange.models import ExchangeRequest


class BuyerFilter(SimpleListFilter):
    title = _('Buyer')
    parameter_name = 'buyer'

    def lookups(self, request, model_admin):
        buyers = ExchangeRequest.objects.values('user', 'user__username').distinct()
        return [(buyer['user'], buyer['user__username']) for buyer in buyers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user=self.value())
        return queryset
