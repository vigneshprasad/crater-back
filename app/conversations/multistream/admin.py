from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin

from conversations.multistream import models


@admin.register(models.MultiStream)
class MultiStreamAdmin(admin.ModelAdmin):

    list_display = ("id", "title", "category", "streams_list", "is_active")
    raw_id_fields = ("streams",)
    list_filter = (
        AutocompleteFilterFactory("Group", "streams"),
        "category"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def streams_list(obj):
        return ["{} - {}".format(stream.id, stream.topic.name) for stream in obj.streams.all()]
