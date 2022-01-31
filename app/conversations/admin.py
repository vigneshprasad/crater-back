from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.utils.html import format_html
from rangefilter import filter
from django_admin_row_actions import AdminRowActionsMixin

from conversations import models
from conversations import tasks


@admin.register(models.SuggestedTopic)
class SuggestedTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "suggested_by", "is_approved")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "image", "is_active")
    search_fields = ("name", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "color", "color_example")
    search_fields = ("name", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "type",
        "all_speakers",
        "attendees_count",
        "start",
        "is_featured",
        "is_live",
        "closed",
        "is_published"
    )
    actions = ("add_previous_webinar_attendees", )
    raw_id_fields = ("speakers", "attendees", "host", )
    readonly_fields = (
        "closed_at",
        "approved_at",
        "last_live_at"
    )
    search_fields = ("speakers__email", "speakers__name", "speakers__username", )
    list_editable = ("is_published", "is_featured", "is_live", "closed", )
    list_filter = (
        ("start", filter.DateRangeFilter),
        "topic"
    )
    exclude = ("interests", "created_at", "deleted_at", "updated_at", "is_deleted")

    def save_model(self, request, obj, form, change):
        if not change:
            return super(GroupAdmin, self).save_model(request, obj, form, change)

        fields_changed = form.changed_data
        cleaned_data = form.cleaned_data
        if "is_approved" in fields_changed:
            if cleaned_data["is_approved"]:
                obj.approve()

        if "is_live" in fields_changed:
            if cleaned_data["is_live"]:
                obj.mark_live(user=request.user)
            else:
                obj.mark_inactive(user=request.user)

        if "closed" in fields_changed:
            if cleaned_data["closed"]:
                obj.mark_closed(user=request.user)

        return super(GroupAdmin, self).save_model(request, obj, form, change)

    def add_previous_webinar_attendees(self, request, queryset):
        """Adds previous webinar attendees to the provided webinar.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of webinars we want
                to add previous attendees to.

        """
        # Delay the task for adding attendees.
        group_ids = list(queryset.values_list("id", flat=True))
        tasks.add_previous_attendees_to_groups.delay(group_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["added_previous_attendees"]}}]
            )

        self.message_user(
            request,
            "Past attendees added to groups: {}".format(
                ", ".join([str(group.id) for group in queryset])
            ),
            messages.SUCCESS
        )

    add_previous_webinar_attendees.short_description = "Add previous attendees"

    @staticmethod
    def all_speakers(obj):
        return [speaker.__str__() for speaker in obj.speakers.all()]

    @staticmethod
    def speaker_count(obj):
        return obj.speakers.count()

    @staticmethod
    def attendees_count(obj):
        return obj.attendees.count()

    @staticmethod
    def get_rangefilter_start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Start Date"


@admin.register(models.Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "invitee",
        "inviter",
        "status"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requester",
        "participant_type",
        "group",
        "group_type",
        "status"
    )
    raw_id_fields = ("requester", "group", )
    search_fields = ("requester__username", "requester__name")
    list_filter = (
        ("created_at", filter.DateRangeFilter),
        ("group__start", filter.DateRangeFilter),
        "group"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "group"
        )

    @staticmethod
    def group_type(obj):
        group_type_dict = dict(models.Group.GROUP_TYPE_CHOICES)
        return group_type_dict.get(obj.group.type)

    @staticmethod
    def get_rangefilter_group__start_title(request, field_path="group__start"):
        """Returns the title for the start date filter."""
        return "Group Start Filter"

    @staticmethod
    def get_rangefilter_created_at_title(request, field_path="created_at"):
        """Returns the title for the start date filter."""
        return "RSVP'd at Filter"


@admin.register(models.GroupLiveLog)
class GroupLiveLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "user",
        "live_status",
        "created_at"
    )
    search_fields = ("user",)
    list_filter = ("group",)
    exclude = ("deleted_at", "updated_at", "is_deleted")


@admin.register(models.GroupRecording)
class GroupRecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "recording",
        "order",
        "status",
        "all_dyte_recordings",
        "is_published"
    )
    list_editable = ("is_published", )
    actions = ("add_previous_webinar_attendees",)
    raw_id_fields = ("group", "dyte_recordings")
    search_fields = (
        "group__host__username",
        "group__host__name",
    )
    list_filter = (
        ("created_at", filter.DateRangeFilter),
        ("group__start", filter.DateRangeFilter),
        "group"
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            "dyte_recordings"
        )

    def save_model(self, request, obj, form, change):
        if not change:
            return super(GroupRecordingAdmin, self).save_model(request, obj, form, change)

        fields_changed = form.changed_data
        cleaned_data = form.cleaned_data
        if "is_published" in fields_changed:
            if cleaned_data["is_published"]:
                obj.publish()

        return super(GroupRecordingAdmin, self).save_model(request, obj, form, change)

    @staticmethod
    def all_dyte_recordings(obj):
        dyte_recordings = [
            dyte_recording.object_url for dyte_recording in obj.dyte_recordings.all()
        ]
        return format_html(" ||| ".join(dyte_recording for dyte_recording in dyte_recordings))

    @staticmethod
    def status(obj):
        return ", ".join([dyte_recording.status for dyte_recording in obj.dyte_recordings.all()])

    @staticmethod
    def get_rangefilter_group__start_title(request, field_path="group__start"):
        """Returns the title for the start date filter."""
        return "Group Start Filter"

    @staticmethod
    def get_rangefilter_created_at_title(request, field_path="created_at"):
        """Returns the title for the start date filter."""
        return "Created at Filter"


@admin.register(models.GroupRtmp)
class GroupRtmpAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "link",
        # "linkedin",
        # "facebook",
        # "twitter",
        # "instagram"
    )
    # list_editable = ("linkedin", "facebook", "twitter", "instagram")
    search_fields = (
        "group__host__username",
        "group__host__name",
    )
    list_filter = (
        ("group__start", filter.DateRangeFilter),
        "group",
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")


@admin.register(models.GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "sender",
        "get_message_data"
    )
    raw_id_fields = ("sender", )
    search_fields = (
        "message",
        "sender"
    )
    list_filter = (
        "group",
        "sender"
    )
    exclude = ("updated_at",)


@admin.register(models.ChatReaction)
class ChatReactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")


@admin.register(models.Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "host",
        "start",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = (
        "host__name",
        "topic__name",
    )
    list_filter = (
        ("start", filter.DateRangeFilter),
    )
