from django.contrib import admin

from crater.creator import models


@admin.register(models.Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "order",
        "number_of_subscribers",
        "certified",
        "type",
        "follower_count",
        "is_active"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").order_by("-order")


@admin.register(models.Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "creator",
        "is_default",
        "is_active"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "community",
        "user"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "user",
        "unfollowed",
        "followed_at"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
