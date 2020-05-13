from django.contrib import admin
from django.contrib.admin import register
from payment.models import BankDetails


@register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_customer_id')
    icon_name='payment'

    def has_add_permission(self, request, obj=None):
        return False
