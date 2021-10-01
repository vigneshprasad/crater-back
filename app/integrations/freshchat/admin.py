from django.contrib import admin

from integrations.freshchat import models


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message_id",
        "user",
        "template_name",
        "template_data",
        "status",
        "failure_info"
    )
    search_fields = ("user__username", "user__name")
    list_filter = ("status", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
