from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from utils.mixins import ViewActionMixin

from users import models
from users.filters import GroupNameAdminFilter
from users.filters import GroupNameUserFilter
from users.filters import RefererFilter
from users.forms import AdminCreationForm
from users.forms import ProfileForm
from users.forms import UserForm
from users.models import Admin
from users.models import CoverFile
from users.models import Profile
from users.models import Referral

admin.site.unregister(Group)


@admin.register(models.BaseSource)
class BaseSourceAdmin(admin.ModelAdmin):
    exclude = ("is_deleted", "deleted_at")


@admin.register(models.Source)
class SourceAdmin(admin.ModelAdmin):
    exclude = ("is_deleted", "deleted_at")


class ProfileAdmin(admin.StackedInline):
    model = Profile
    form = ProfileForm


@admin.register(get_user_model())
class UserAdmin(ViewActionMixin, admin.ModelAdmin):
    class Media:
        css = {
            "all": ("css/stacked-full-width.css",)
        }

    list_action_text = _("View profile")
    list_display_links = ("action", "username")
    edit_icon = "launch"
    icon_name = "person"
    list_display = ("username", "name", "email", "group", "score", "date_joined", "is_active", "action")
    list_editable = ["is_active", ]
    search_fields = ("username", "name", "email", "phone_number")
    list_filter = ("is_active", GroupNameUserFilter, )
    form = UserForm
    fieldsets = (
        ("Approvals", {
            "fields": (
                ("is_active", "groups"),
            ),
        }),
        ("User Data", {
            "fields": (
                ("name", "email"),
                ("username", "phone_number"),
                "score"
            ),
        }),
    )
    inlines = [ProfileAdmin]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups").filter(
            is_superuser=False, is_staff=False
        )

    @staticmethod
    def group(user):
        if not user.groups.exists():
            return mark_safe("<i class='material-icons red-color medium-icon'>highlight_off</i>")
        return ", ".join([group.name for group in user.groups.all()])


@admin.register(Admin)
class AdminAdmin(ViewActionMixin, admin.ModelAdmin):
    list_action_text = _("View profile")
    edit_icon = "launch"
    icon_name = "verified_user"

    form = AdminCreationForm
    list_display = ("name", "email", "is_superuser", "is_active", "all_groups", "action")
    list_filter = ("is_superuser", GroupNameAdminFilter)
    search_fields = ("name", "email")
    list_editable = ("name", "is_superuser")

    @staticmethod
    def all_groups(user_admin):
        return ", ".join(user_admin.groups.values_list("name", flat=True))

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(is_superuser=True) | Q(is_staff=True))


@admin.register(Referral)
class ReferralAdmin(ViewActionMixin, admin.ModelAdmin):
    list_display = ["referer_name", "referral_name", "created", "amount", "is_paid", "is_rewarded", "action"]
    list_editable = ["amount", "is_paid", "is_rewarded"]
    readonly_fields = ["user"]
    list_filter = ["is_paid", "is_rewarded", "created", RefererFilter]
    search_fields = ["user__name"]
    icon_name = "nature_people"

    @staticmethod
    def referral_name(referral):
        href = reverse("admin:users_user_change", args=(referral.user.pk,))
        link = f"<a href='{href}'>{referral.user.name}</a>"
        return mark_safe(link)

    @staticmethod
    def referer_name(referral):
        if not referral.user.referer or referral.user.referer.is_superuser:
            return referral.user.referer

        if get_user_model().objects.filter(pk=referral.user.referer.pk).exists():
            href = reverse("admin:users_user_change", args=(referral.user.referer.pk,))
        else:
            href = reverse("admin:users_admin_change", args=(referral.user.referer.pk,))
        link = f"<a href='{href}'>{referral.user.referer.name}</a>"
        return mark_safe(link)

    def has_add_permission(self, request):
        return False


@admin.register(Group)
class GroupAdmin(GroupAdmin):
    list_display = ("name", "count")

    @staticmethod
    def count(group):
        return group.user_set.count()

    def get_queryset(self, request):
        return super().get_queryset(request)

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(CoverFile)
class CoverFileAdmin(ViewActionMixin, admin.ModelAdmin):
    icon_name = "person"
    list_display = ["user", "file"]
    list_display_links = None

    def get_queryset(self, request):
        return super().get_queryset(request).all()


@admin.register(models.ProfileExtraInfoMeta)
class ProfileExtraMetaAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "tag")


@admin.register(models.UserReferral)
class UserReferralAdmin(admin.ModelAdmin):
    list_display = ("user", "referrer", "amount", "status")
    search_fields = ("user__username", "user__name", "referrer__username", "referrer__name")
    exclude = ("created_at", "updated_at", "deleted_at", "is_deleted")
