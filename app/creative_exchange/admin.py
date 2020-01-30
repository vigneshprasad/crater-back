from django.contrib import admin
from django.contrib.admin import register
from django.utils.translation import ugettext_lazy as _

from utils.mixins import ViewActionMixin
from . import models
from .filters import BuyerFilter


@register(models.ExchangeRequest)
class ExchangeAdmin(ViewActionMixin, admin.ModelAdmin):
    icon_name = 'track_changes'
    list_display = ['job_name', 'buyer', 'service_type', 'created', 'extended_price', 'applied', 'is_deleted', 'action']
    list_editable = ['is_deleted']
    list_filter = [BuyerFilter, 'created']
    search_fields = ['category__name']
    actions = ['mark_as_deleted']

    def job_name(self, exchange):
        return exchange.title
    job_name.short_description = _('Job Name')

    def buyer(self, exchange):
        return exchange.user.name
    buyer.short_description = _('Buyer')

    def service_type(self, exchange):
        return exchange.category.name
    service_type.short_description = _('Service Type')

    def applied(self, exchange):
        return exchange.quotes.count()
    applied.short_description = _('Sellers Applied')

    def mark_as_deleted(self, request, queryset):
        queryset.update(is_deleted=True)
    mark_as_deleted.short_description = _('Mark selected items as deleted')


@register(models.ExchangeCategory)
class ExchangeCategoryAdmin(admin.ModelAdmin):
    icon_name = 'track_changes'
