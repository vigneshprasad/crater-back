from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.contrib.admin import register
from django.utils.html import format_html
from django_admin_row_actions import AdminRowActionsMixin
from django_object_actions import DjangoObjectActions
from rangefilter import filter

from conversations.group_helpers import models


@register(models.Viewer)
class ViewerAdmin(DjangoObjectActions, AdminRowActionsMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "group",
        "start",
        "creator",
        # "live",
        # "closed",
        # "published",
        "count"
    )
    raw_id_fields = ("group", )
    list_editable = ("count", )
    list_filter = (
        AutocompleteFilterFactory("Group", "group"),
        "group__is_live",
        "group__closed",
        "group__is_published",
        ("group__start", filter.DateRangeFilter),
    )
    change_actions = ("increase", "decrease")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def increase(self, request, obj):
        return obj.increment()
    increase.label = format_html("<span style='color: {};'>{}</span>", "#008000", "Increase (+1)")
    increase.short_description = "Increase count by 1"

    def decrease(self, request, obj):
        return obj.decrement()
    decrease.label = format_html("<span style='color: {};'>{}</span>", "#FF0000", "Decrease (-1)")
    decrease.short_description = "Decrease count by 1"

    @staticmethod
    def creator(obj):
        return obj.group.host

    def start(self, obj):
        return obj.group.start
    start.short_description = "Stream Start"
    start.admin_order_field = "group__start"

    def closed(self, obj):
        return obj.group.closed
    closed.boolean = True

    def live(self, obj):
        return obj.group.is_live
    live.boolean = True

    def published(self, obj):
        return obj.group.is_published
    published.boolean = True

    @staticmethod
    def get_rangefilter_group__start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Group Start"

    def get_row_actions(self, obj):
        """Returns row action objects for the admin changelist."""
        row_actions = [
            {
                "divided": True,
                "label": format_html(
                    "<span style='color: {};'>{}</span>",
                    "#008000",
                    "Increase (+1)"
                ),
                "action": "increment",
                "tooltip": "Increase count by 1."
            },
            {
                "divided": True,
                "label": format_html(
                    "<span style='color: {};'>{}</span>",
                    "#FF0000",
                    "Decrease (-1)"
                ),
                "action": "decrement",
                "tooltip": "Decrease count by 1."
            }
        ]
        row_actions += super(ViewerAdmin, self).get_row_actions(obj)

        return row_actions
