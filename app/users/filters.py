from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from users import constants


class GroupNameAdminFilter(SimpleListFilter):
    title = _("Group")
    parameter_name = "group"

    def lookups(self, request, model_admin):
        return (
            ("admin", _("Admin")),
            ("support", _("Support")),
        )

    def queryset(self, request, queryset):
        if self.value() == "admin":
            return queryset.filter(groups__name="Admin")
        if self.value() == "support":
            return queryset.filter(groups__name="Support")


class GroupNameUserFilter(SimpleListFilter):
    title = _("Group")
    parameter_name = "group"

    def lookups(self, request, model_admin):
        return (
            (constants.USER_GROUP, constants.USER_GROUP),
            (constants.INVESTOR_GROUP, constants.INVESTOR_GROUP),
            (constants.CRATER_CLUB_GROUP, constants.CRATER_CLUB_GROUP),
            (constants.WORKNETWORK_GROUP, constants.WORKNETWORK_GROUP)
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset.all()
        return queryset.filter(groups__name=self.value())


class RefererFilter(SimpleListFilter):
    title = _("Referer")
    parameter_name = "referer"

    def lookups(self, request, model_admin):
        referrers = get_user_model().objects.filter(referrals__isnull=False)
        return [(referrer.email, referrer.name) for referrer in referrers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__referer__email=self.value())
        return queryset
