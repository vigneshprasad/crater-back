from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages

from conversations.multistream import models
from integrations.dyte import tasks as dyte_tasks


@admin.register(models.MultiStream)
class MultiStreamAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "category",
        "streams_list",
        "active_streams",
        "inactive_streams",
        "is_active"
    )
    raw_id_fields = ("streams",)
    list_filter = (
        AutocompleteFilterFactory("Group", "streams"),
        "category"
    )
    actions = ("start_livestream_for_multistream", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def streams_list(obj):
        return ["{}".format(stream.id) for stream in obj.streams.all()]

    @staticmethod
    def active_streams(obj):
        return ["{}".format(stream.id) for stream in obj.streams.filter(session_active=True)]

    @staticmethod
    def inactive_streams(obj):
        return ["{}".format(stream.id) for stream in obj.streams.filter(session_active=False)]

    def start_livestream_for_multistream(self, request, queryset):
        """Starts livestream for a multistream.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of multistream we want to
                start livestream for.

        Note:
            This action runs for only one multistream at a time.

        """
        if queryset.count() > 1:
            return self.message_user(
                request,
                "Please select only one multistream at a time for starting livestream",
                messages.ERROR
            )

        multistream = queryset.first()
        dyte_tasks.start_livestream_for_multistream.apply_async(
            args=(multistream.id,),
            countdown=10
        )

        # If starting a recording is successful
        self.log_change(
            request,
            multistream,
            message=[{"changed": {"actions": ["start_livestream_for_multistream"]}}]
        )
        groups = multistream.streams.all()
        self.message_user(
            request,
            "Started livestreams for groups: {}".format(", ".join([str(group.id) for group in groups])),
            messages.SUCCESS
        )

    start_livestream_for_multistream.short_description = "Start HLS for multistream"
