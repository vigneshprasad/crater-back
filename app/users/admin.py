from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from users.filters import GroupNameAdminFilter, GroupNameUserFilter, RefererFilter
from users.forms import AdminCreationForm, UserForm, ProfileForm
from users.models import Profile, Admin, Referral
from utils.mixins import ViewActionMixin

admin.site.unregister(Group)


class ProfileAdmin(admin.StackedInline):
    model = Profile
    form = ProfileForm
    autocomplete_fields = ['work_city']


@admin.register(get_user_model())
class UserAdmin(ViewActionMixin, admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/stacked-full-width.css',)
        }

    list_action_text = _('View profile')
    list_display_links = ('action', 'name')
    edit_icon = 'launch'
    icon_name = 'person'
    list_display = ('name', 'email', 'group', 'date_joined', 'status', 'is_active', 'action')
    list_editable = ['is_active']
    search_fields = ('name', 'email')
    list_filter = ('is_active', GroupNameUserFilter, 'is_approved')
    form = UserForm
    fieldsets = (
        ('Approvals', {
            'fields': (('is_active', 'groups'), ('is_approved', 'is_service_approved'),),
        }),
        ('User Data', {
            'fields': (('name', 'email'), ('city', 'phone_number'), ('referer', 'phone_number_verified'), 'rating'),
        }),
    )
    autocomplete_fields = ['city']
    readonly_fields = ['referer', 'rating']
    inlines = [ProfileAdmin]

    @staticmethod
    def status(user):
        if not user.is_active:
            return _('Banned')

        if user.is_approved:
            return _('Approved')
        return _('Pending')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_superuser=False, is_staff=False)

    @staticmethod
    def group(user):
        if not user.groups.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([group.name for group in user.groups.all()])


@admin.register(Admin)
class AdminAdmin(ViewActionMixin, admin.ModelAdmin):
    list_action_text = _("View profile")
    edit_icon = 'launch'
    icon_name = 'verified_user'

    form = AdminCreationForm
    list_display = ('name', 'email', 'is_superuser', 'is_active', 'group', 'action')
    list_filter = ('is_superuser', GroupNameAdminFilter)
    search_fields = ('name', 'email')
    list_editable = ('name', 'is_superuser')

    @staticmethod
    def group(user_admin):
        return user_admin.groups.first()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(is_superuser=True) | Q(is_staff=True))


@admin.register(Referral)
class ReferralAdmin(ViewActionMixin, admin.ModelAdmin):
    list_display = ['referer_name', 'referral_name', 'created', 'amount', 'is_paid', 'is_rewarded', 'action']
    list_editable = ['amount', 'is_paid', 'is_rewarded']
    readonly_fields = ['user']
    list_filter = ['is_paid', 'is_rewarded', 'created', RefererFilter]
    search_fields = ['user__name']
    icon_name = 'nature_people'

    @staticmethod
    def referral_name(referral):
        href = reverse("admin:users_user_change", args=(referral.user.pk,))
        link = f'<a href="{href}">{referral.user.name}</a>'
        return mark_safe(link)

    @staticmethod
    def referer_name(referral):
        if not referral.user.referer or referral.user.referer.is_superuser:
            return referral.user.referer

        if get_user_model().objects.filter(pk=referral.user.referer.pk).exists():
            href = reverse("admin:users_user_change", args=(referral.user.referer.pk,))
        else:
            href = reverse("admin:users_admin_change", args=(referral.user.referer.pk,))
        link = f'<a href="{href}">{referral.user.referer.name}</a>'
        return mark_safe(link)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(Group)
class GroupAdmin(GroupAdmin):
    list_display = ('name', 'count')
    readonly_fields = ['name']

    @staticmethod
    def count(group):
        return group.user_set.count()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(name__in=['Admin', 'Support'])

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
