from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.utils.html import format_html
from django_admin_row_actions import AdminRowActionsMixin
from rangefilter import filter

from conversations import models, tasks
from integrations.dyte import tasks as dyte_tasks


@admin.register(models.SuggestedTopic)
class SuggestedTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "suggested_by", "is_approved")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image", "is_active")
    fields = (
        "name",
        "image",
        "description",
        "is_active",
        "is_approved",
        "is_suggested",
        "parent"
    )
    list_editable = ("name", )
    raw_id_fields = ("parent", )
    search_fields = ("name",)
    exclude = ("creator", "article", "created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "color", "color_example", "show_on_home_page")
    search_fields = ("name",)
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_editable = ("is_active", "show_on_home_page")


@admin.register(models.Group)
class GroupAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "type",
        "host",
        # "all_speakers",
        "attendees_count",
        "start",
        "is_featured",
        "is_live",
        "closed",
        "is_published",
        "is_rescheduled",
        "is_obs",
        "viewer_count",
        "host_poc",
    )
    fieldsets = (
        (
            ("Display Details", {
                "fields": (
                    ("type", "categories"),
                    "topic",
                    "description",
                    ("is_featured", "is_published"),
                    "start",
                    "end",
                ),
            }),
            ("Members", {
                "fields": (
                    ("host", "speakers"),
                    "attendees",
                ),
            }),
            ("Status", {
                "fields": (
                    ("is_live", "closed"),
                    ("is_rescheduled", "is_obs"),
                    ("is_approved", "is_full")
                )
            }),
            ("Privacy", {
                "fields": (
                    ("max_speakers", "max_attendees"),
                    ("privacy", "medium")
                )
            }),
            ("Stats", {
                "fields": (
                    "total_minutes_spent_by_attendees",
                    "total_minutes_spent_by_host",
                )
            }),
            ("Logs", {
                "fields": (
                    ("last_live_at", "closed_at"),
                    "published_at",
                    ("approved_at", "rescheduled_at"),
                )
            }),
            ("Score", {
                "fields": (
                    ("calculate_score", "score"),
                )
            }),
        )
    )
    actions = ("add_previous_webinar_attendees", "recalculate_minutes_for_groups")
    raw_id_fields = ("speakers", "attendees", "host", "categories")
    readonly_fields = (
        "closed_at",
        "approved_at",
        "last_live_at",
        "rescheduled_at",
        "published_at",
        "score",
        "total_minutes_spent_by_attendees",
        "total_minutes_spent_by_host"
    )
    search_fields = ("id", "speakers__email", "speakers__name", "speakers__username",)
    list_editable = (
        "is_published",
        "is_featured",
        "is_live",
        "closed",
        "is_rescheduled",
        "is_obs"
    )
    list_filter = (
        "closed",
        "is_published",
        ("start", filter.DateRangeFilter),
    )
    exclude = (
        "interests",
        "created_at",
        "deleted_at",
        "updated_at",
        "is_deleted"
    )

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

        if "is_rescheduled" in fields_changed:
            if cleaned_data["is_rescheduled"]:
                obj.mark_rescheduled(user=request.user)

        if "is_published" in fields_changed:
            if cleaned_data["is_published"]:
                obj.mark_published()

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

    def recalculate_minutes_for_groups(self, request, queryset):
        """Recalculate minutes for groups.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of streams we want to
                recalculate minutes for.

        """
        # Delay the task for recalculating minutes.
        group_ids = list(queryset.values_list("id", flat=True))
        dyte_tasks.recalculate_minutes_for_groups.delay(group_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["recalculate_minutes_for_groups"]}}]
            )

        self.message_user(
            request,
            "Recalculated minutes for groups: {}".format(
                ", ".join([str(group.id) for group in queryset])
            ),
            messages.SUCCESS
        )

    recalculate_minutes_for_groups.short_description = "Recalculate minutes"

    @staticmethod
    def all_speakers(obj):
        return [speaker.__str__() for speaker in obj.speakers.all()]

    @staticmethod
    def host_poc(obj):
        if not obj.host:
            return ""
        if not obj.host.is_creator:
            return ""
        return obj.host.creator.point_of_contact

    def viewer_count(self, obj):
        if not obj.host:
            return False
        if not hasattr(obj.host, "permission"):
            return False
        return obj.host.permission.show_viewer_count

    viewer_count.boolean = True

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
    raw_id_fields = ("requester", "requester",)
    list_select_related = ("requester", "group__host", "group__topic")
    search_fields = ("requester__username", "requester__name")
    list_filter = (
        ("created_at", filter.DateRangeFilter),
        AutocompleteFilterFactory("Group", "group", use_pk_exact=True),
        ("group__start", filter.DateRangeFilter)
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

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
    raw_id_fields = ("group", "user")
    search_fields = ("user__name", "user__email", "user__username")
    list_filter = ("group",)
    exclude = ("deleted_at", "updated_at", "is_deleted")


@admin.register(models.GroupRecording)
class GroupRecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "recording",
        "status",
        "all_dyte_recordings",
        "latest_recording_file_size",
        "is_published",
        "featured",
    )
    list_editable = ("is_published", "featured",)
    actions = ("publish_group_recordings", "update_dyte_recording_status")
    raw_id_fields = ("group", "dyte_recordings")
    search_fields = (
        "group__host__username",
        "group__host__name",
    )
    list_filter = (
        AutocompleteFilterFactory("Group", "group"),
        "featured",
        "is_published"
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")

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
    def latest_recording_file_size(obj):
        """Returns recording file size in MB for the last recording.

        Note:
            It shows the file size of the recording that is published
                for a group recording.

        """
        dyte_recording = obj.dyte_recordings.last()
        if not dyte_recording or dyte_recording.file_size_mb:
            return None
        return dyte_recording.file_size_mb

    @staticmethod
    def status(obj):
        return ", ".join([dyte_recording.status for dyte_recording in obj.dyte_recordings.all()])

    def update_dyte_recording_status(self, request, queryset):
        """Adds previous webinar attendees to the provided webinar.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of group recording we are
                update the dyte recording status for.

        """
        dyte_recording_ids = []
        for obj in queryset:
            dyte_recording_ids = dyte_recording_ids + list(obj.dyte_recordings.values_list("id", flat=True))

        dyte_tasks.update_meeting_recording_status_for_recording_ids.delay(dyte_recording_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["update_dyte_recording_status"]}}]
            )

        self.message_user(
            request,
            "Dyte Recording status updated for: {}".format(
                ", ".join([str(group_recording.id) for group_recording in queryset])
            ),
            messages.SUCCESS
        )

    update_dyte_recording_status.short_description = "Update Dyte Recording Status"

    def publish_group_recordings(self, request, queryset):
        """Marks group recordings as published and uploads
            recordings to live_stream_recording s3 bucket.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of group recording we want
                to publish.

        """
        # Delay the task for adding attendees.
        group_recording_ids = list(queryset.values_list("id", flat=True))
        tasks.publish_group_recordings.delay(group_recording_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["marked_publish_uploaded_live_stream_recording"]}}]
            )

        self.message_user(
            request,
            "Marked Group Recordings as Published. Uploaded to S3: {}".format(
                ", ".join([str(group.id) for group in queryset])
            ),
            messages.SUCCESS
        )

    publish_group_recordings.short_description = "Publish Group Recordings"

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
        "link"
    )
    raw_id_fields = ("group",)
    search_fields = ("group__id",)
    exclude = ("deleted_at", "updated_at", "is_deleted")

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)


@admin.register(models.GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "sender",
        "display_name",
        "get_message_data"
    )
    raw_id_fields = ("group", "sender",)
    search_fields = (
        "message",
        "sender__name",
        "sender__email",
        "sender__username"
    )
    list_filter = (
        AutocompleteFilterFactory("Group", "group", use_pk_exact=True),
    )
    exclude = ("updated_at",)

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)


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
        "is_published",
    )
    raw_id_fields = ("host", "groups")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = (
        "host__name",
        "topic__name",
    )
    list_filter = (
        ("start", filter.DateRangeFilter),
    )
    list_editable = ("is_published",)


@admin.register(models.GroupQuestion)
class GroupQuestion(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "sender",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    raw_id_fields = ("group", "sender",)
    search_fields = (
        "question",
        "sender__name",
        "sender__email",
        "sender__username"
    )
    list_filter = ("group",)


@admin.register(models.QuestionUpvote)
class QuestionUpvoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "user",
        "upvote",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    raw_id_fields = ("question", "user",)
