from django.contrib import admin

from crater.payments import models


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "gateway")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
