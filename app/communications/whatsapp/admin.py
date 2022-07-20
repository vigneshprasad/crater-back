from django.contrib import admin

from communications.whatsapp import models


@admin.register(models.WhatsappProvider)
class WhatsappProviderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "message_type",
        "provider",
        "updated_at"
    )
    list_filter = ("provider", )
    exclude = ("created_at", "deleted_at", "is_deleted")
