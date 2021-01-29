from django.contrib import admin
from group_meetings import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "creator", "category", "is_approved", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "host",
        "agenda",
        "start",
        "privacy",
        "closed",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


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
        "group",
        "requester",
        "status",
        "is_recommended"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
