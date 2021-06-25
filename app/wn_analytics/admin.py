from django.contrib.admin import register, ModelAdmin
from .models import TrackLog, IdentifyLog, UserSource


@register(TrackLog)
class TrackLogAdmin(ModelAdmin):
    list_display = (
        "user",
        "event"
    )
    search_fields = ["user"]
    readonly_fields = ["user", "event"]


@register(IdentifyLog)
class IdentifyLogAdmin(ModelAdmin):
    list_display = (
        "user",
    )
    search_fields = ["user"]
    readonly_fields = ["user"]


@register(UserSource)
class UserSourceAdmin(ModelAdmin):
    list_display = (
        "user",
        "utm_source",
        "utm_campaign",
    )
    search_fields = ["user", "utm_source", "utm_campaign"]
    readonly_fields = ["user"]
