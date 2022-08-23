from django.contrib.admin import ModelAdmin, register

from communications.emails import models


@register(models.EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    list_display = ("id", "name", "subject", "from_email", "service")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ("id", "user", "email_template", "email_message_id", "sent_at")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
