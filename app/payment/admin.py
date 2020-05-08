from django.contrib import admin
from django.contrib.admin import register
from payment.models import BankDetails


@register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    pass
