from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from order.models import Order


class BuyerFilter(SimpleListFilter):
    title = _('Buyer')
    parameter_name = 'buyer'

    def lookups(self, request, model_admin):
        buyers = Order.objects.values('buyer', 'buyer__name').distinct()
        return [(buyer['buyer'], buyer['buyer__name']) for buyer in buyers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(buyer=self.value())
        return queryset


class SellerFilter(SimpleListFilter):
    title = _('Seller')
    parameter_name = 'seller'

    def lookups(self, request, model_admin):
        buyers = Order.objects.values('seller', 'seller__name').distinct()
        return [(buyer['seller'], buyer['seller__name']) for buyer in buyers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(seller=self.value())
        return queryset
