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
        "is_active",
        "slug",
        "show_club_members",
    )
    raw_id_fields = ("user", )
    list_filter = ("certified", "is_active")
    search_fields = ("user__name", "user__username")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").order_by("-order")


@admin.register(models.Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "display"
    )

    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "creator",
        "is_default",
        "is_active"
    )
    list_filter = ("creator",)
    search_fields = (
        "creator__user__username",
        "creator__user__name"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "community",
        "joined_at"
    )
    search_fields = (
        "user__username",
        "user__name"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "creator",
        "notify",
        "unfollowed",
    )
    list_filter = ("creator", )
    list_editable = ("notify", "unfollowed")
    search_fields = (
        "creator__user__username",
        "creator__user__name",
        "user__username",
        "user__name"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
