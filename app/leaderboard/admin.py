from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages

from leaderboard import models, tasks


@admin.register(models.DurationType)
class DurationTypeAdmin(admin.ModelAdmin):

    model = models.DurationType
    list_display = ("id", "name", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Challenge)
class ChallengeAdmin(admin.ModelAdmin):

    model = models.Challenge
    list_display = ("id", "name", "title", "all_categories", "all_duration_types", "is_active")
    raw_id_fields = ("participants", "categories")
    list_editable = ("is_active", )
    search_fields = (
        "name",
        "title",
        "id"
    )
    list_filter = (
        "is_active",
        "duration_types"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def all_categories(obj):
        return [category.__str__() for category in obj.categories.all()]

    @staticmethod
    def all_duration_types(obj):
        return [duration.__str__() for duration in obj.duration_types.all()]

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)


@admin.register(models.Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):

    model = models.Leaderboard
    list_display = ("id", "challenge", "duration_type", "start", "end", "is_active")
    raw_id_fields = ("participants", "challenge")
    list_editable = ("is_active", )
    search_fields = (
        "challenge__title",
        "challenge__id",
        "id",
        "participants__username",
        "participants__name",
    )
    list_filter = (
        "is_active",
        "duration_type",
        AutocompleteFilterFactory("Challenge", "challenge"),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ("add_challenge_participants", "recalculate_leaderboard")

    @staticmethod
    def all_participants(obj):
        return [participant.__str__() for participant in obj.participants.all()]

    def add_challenge_participants(self, request, queryset):
        """Add challenge participants."""
        leaderboard_ids = list(queryset.values_list("id", flat=True))
        tasks.add_challenge_participants.delay(leaderboard_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["add_challenge_participant"]}}]
            )

        self.message_user(
            request,
            "Participants added to leaderboards: {}".format(
                ", ".join([str(leaderboard.id) for leaderboard in queryset])
            ),
            messages.SUCCESS
        )

    add_challenge_participants.short_description = "Add all challenge participants"

    def recalculate_leaderboard(self, request, queryset):
        """Recalculate leaderboard."""
        leaderboard_ids = list(queryset.values_list("id", flat=True))
        tasks.recalculate_leaderboards.delay(leaderboard_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["recalculate_leaderboards"]}}]
            )

        self.message_user(
            request,
            "Recalculated leaderboards: {}".format(
                ", ".join([str(leaderboard.id) for leaderboard in queryset])
            ),
            messages.SUCCESS
        )

    recalculate_leaderboard.short_description = "Recalculate minutes for Leaderboard"

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)


@admin.register(models.UserLeaderboard)
class UserLeaderboardAdmin(admin.ModelAdmin):

    model = models.UserLeaderboard
    list_display = ("id", "leaderboard", "user", "total_minutes", "rank", "is_active")
    raw_id_fields = ("leaderboard", "user", )
    list_editable = ("is_active", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "leaderboard__duration_type",
        AutocompleteFilterFactory("Leaderboard", "leaderboard"),
    )

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)
