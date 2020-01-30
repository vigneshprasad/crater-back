from django.contrib.admin import ModelAdmin, register
from django.urls import reverse
from django.utils.safestring import mark_safe

from order.filters import BuyerFilter, SellerFilter
from order.models import Order
from django.utils.translation import ugettext_lazy as _


@register(Order)
class OrderAdmin(ModelAdmin):
    icon_name = 'work'
    list_display = ('job_order', 'created', '_buyer', '_seller', 'status', 'sum', 'is_paid', 'job_state')
    list_editable = ['is_paid']
    readonly_fields = [
        'uuid', 'buyer', 'seller', 'quote', 'service', 'note', 'order_field', 'completed_file',  'rate', 'review_text',
        # 'status'
    ]
    list_filter = ['created', 'is_paid', 'status', BuyerFilter, SellerFilter]

    @staticmethod
    def job_order(order):
        if order.service and order.service.service_type:
            return order.service.service_type.name

    @staticmethod
    def sum(order):
        if order.quote:
            return order.quote.price
        return '-'

    @staticmethod
    def job_state(order):
        if order.status == 'complete':
            return _('Completed') if order.is_paid else _('Waiting for payment')
        if order.status == 'canceled':
            return _('Refunded') if order.is_paid else _('Waiting for refund')
        return _('Pending')

    @staticmethod
    def _buyer(order):
        href = reverse("admin:users_user_change", args=(order.buyer.pk,))
        return mark_safe(f'<a target="_blank" href="{href}">{order.buyer.name}</a>')

    @staticmethod
    def _seller(order):
        href = reverse("admin:users_user_change", args=(order.seller.pk,))
        return mark_safe(f'<a target="_blank" href="{href}">{order.seller.name}</a>')

    def has_add_permission(self, request):
        return False
