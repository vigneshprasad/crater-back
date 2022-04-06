from django.contrib import admin, messages

from leaderboard import models
from leaderboard import tasks


class ChallengeAdmin(admin.ModelAdmin):

    model = models.Challenge
    list_display = ("id", "name", "title", "all_categories", "duration_types", "is_active")
    list_editable = ("is_active", )

    # def save_model(self, request, obj, form, change):
    #     result = super(ChallengeAdmin, self).save_model(request, obj, form, change)
    #     if not change:
    #         fields_changed = form.changed_data
    #         cleaned_data = form.cleaned_data
    #         if "duration_types" in fields_changed:
    #             if cleaned_data["duration_types"]:
    #                 duration_type = cleaned_data["duration_types"]
    #                 # tasks.create_leaderboards_for_duration_types(obj)
    #     return result

    @staticmethod
    def all_categories(obj):
        return [category.__str__() for category in obj.categories.all()]


class LeaderboardAdmin(admin.ModelAdmin):

    model = models.Leaderboard
    list_display = ("id", "challenge", "duration_type", "all_participants", "start", "end", "is_active")
    list_editable = ("is_active", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ("add_challenge_participants", )

    @staticmethod
    def all_participants(obj):
        return [participant.__str__() for participant in obj.participants.all()]

    def add_challenge_participants(self, request, queryset):

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


class UserLeaderboardAdmin(admin.ModelAdmin):

    model = models.UserLeaderboard
    list_display = ("id", "leaderboard__challenge", "user", "total_minutes", "rank")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
