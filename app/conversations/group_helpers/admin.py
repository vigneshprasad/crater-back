from django.contrib import admin
from django.contrib.admin import register

from conversations.group_helpers import models


@register(models.Viewer)
class ViewerAdmin(admin.ModelAdmin):

    list_display = ("group", "count")
    raw_id_fields = ("group", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
