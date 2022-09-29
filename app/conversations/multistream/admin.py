from django.contrib import admin

from conversations.multistream import models

# Register your models here.


@admin.register(models.MultiStream)
class MultiStreamAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    raw_id_fields = ("streams",)
