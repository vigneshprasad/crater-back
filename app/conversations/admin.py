from django.contrib import admin

from conversations import models


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "image", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "score",
        "topic",
        "group_speakers",
        "group_interests",
        "start",
        "closed",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = ("speakers__email", )
    list_filter = (
        ("start", admin.DateFieldListFilter),
    )

    @staticmethod
    def group_speakers(obj):
        return ", ".join(speaker.email for speaker in obj.speakers.all())

    @staticmethod
    def group_interests(obj):
        return ", ".join(interest.name for interest in obj.interests.all())


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
