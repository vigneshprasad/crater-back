from django.contrib import admin

from crater.creator import models


@admin.register(models.Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "slug",
        "order",
        "subscriber_count",
        "follower_count",
        "certified",
        "is_active",
        "show_club_members",
        "point_of_contact",
    )
    raw_id_fields = ("user", "point_of_contact")
    list_editable = ("order", "certified", "is_active", "show_club_members")
    list_filter = ("certified", "is_active")
    search_fields = (
        "user__name",
        "user__username",
        "slug",
        "point_of_contact__name",
        "point_of_contact__username"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by("-order")


@admin.register(models.Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "display"
    )
    raw_id_fields = ("creator", )
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
    raw_id_fields = ("creator", )
    list_filter = ("creator",)
    search_fields = (
        "creator__user__username",
        "creator__user__name",
        "creator__slug"
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
    raw_id_fields = ("user", "community")
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
        "unfollowed",
        "followed_at",
        "notify",
    )
    raw_id_fields = ("user", "creator")
    list_filter = ("creator", )
    list_editable = ("notify", "unfollowed")
    search_fields = (
        "creator__user__username",
        "creator__user__name",
        "user__username",
        "user__name"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
