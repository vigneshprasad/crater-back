from django.contrib import admin

# Register your models here.
from leaderboard import models


class LeaderboardAdmin(admin.ModelAdmin):
    model = models.Leaderboard
    list_display = ("id", "title", "all_categories", "type", "start", "end")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


class UserLeaderboardAdmin(admin.ModelAdmin):
    model = models.UserLeaderboard
    list_display = ("id", "user", "total_minutes", "rank")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
