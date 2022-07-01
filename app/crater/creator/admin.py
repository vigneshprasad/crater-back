from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from crater.creator import models


class POCFilter(SimpleListFilter):
    title = "POC"
    parameter_name = "point_of_contact"

    def lookups(self, request, model_admin):
        pocs = set([creator.point_of_contact for creator in model_admin.model.objects.filter(
            point_of_contact__isnull=False
        )])
        lookups_list = [("NULL", "NULL")]
        for poc in pocs:
            lookups_list.append((poc.pk, poc.email))

        return lookups_list

    def queryset(self, request, queryset):
        if self.value() == "NULL":
            return queryset.filter(point_of_contact__isnull=True)
        elif self.value():
            return queryset.filter(point_of_contact_id=self.value())


class ProspectorFilter(SimpleListFilter):
    title = "Prospector"
    parameter_name = "prospector"

    def lookups(self, request, model_admin):
        prospectors = set([creator.prospector for creator in model_admin.model.objects.filter(
            prospector__isnull=False
        )])
        lookups_list = [("NULL", "NULL")]
        for prospector in prospectors:
            lookups_list.append((prospector.pk, prospector.email))

        return lookups_list

    def queryset(self, request, queryset):
        if self.value() == "NULL":
            return queryset.filter(prospector__isnull=True)
        elif self.value():
            return queryset.filter(prospector_id=self.value())


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
        "prospector",
        "show_analytics"
    )
    raw_id_fields = ("user", "point_of_contact", "prospector")
    list_editable = ("order", "certified", "is_active", "show_club_members", "show_analytics")
    list_filter = ("certified", "is_active", POCFilter, ProspectorFilter)
    search_fields = (
        "user__name",
        "user__username",
        "slug",
        "point_of_contact__name",
        "point_of_contact__username",
        "point_of_contact__email",
        "prospector__name",
        "prospector__username",
        "prospector__email",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by("-order")

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)


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

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)
