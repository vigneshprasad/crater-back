from django.contrib.admin import register, ModelAdmin

from wn_analytics import models


@register(models.TrackLog)
class TrackLogAdmin(ModelAdmin):
    list_display = (
        "user",
        "event"
    )
    search_fields = ["user"]
    readonly_fields = ["user", "event"]


@register(models.IdentifyLog)
class IdentifyLogAdmin(ModelAdmin):
    list_display = (
        "user",
    )
    search_fields = ["user"]
    readonly_fields = ["user"]


@register(models.UserSource)
class UserSourceAdmin(ModelAdmin):
    list_display = (
        "user",
        "utm_source",
        "utm_campaign",
        "utm_medium",
    )
    list_filter = (
        "utm_source", 
        "utm_campaign",
        "utm_medium",
    )
    search_fields = ("user__name", "user__username", "user__email", "utm_source", "utm_campaign", "utm_medium")
    readonly_fields = ["user"]
