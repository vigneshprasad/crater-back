from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from users.filters import GroupNameFilter
from users.forms import AdminCreationForm, UserForm
from users.models import Profile, Admin
from utils.mixins import ViewActionMixin
from django.contrib.auth.models import Group
admin.site.unregister(Group)


class ProfileAdmin(admin.StackedInline):
    model = Profile


@admin.register(get_user_model())
class UserAdmin(ViewActionMixin, admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/stacked-full-width.css',)
        }

    list_action_text = _("View profile")
    edit_icon = 'launch'
    icon_name = 'person'
    list_display = ('name', 'email', 'group', 'date_joined', 'status', 'is_active', 'action')
    list_editable = ['is_active']
    search_fields = ('name', 'email')
    list_filter = ('groups__name', 'is_active')
    form = UserForm
    fieldsets = (
        ('Approvals', {
            'fields': (('is_active', 'groups'), ('is_approved', 'is_service_approved'),),
            'classes': ['collapse in']
        }),
        ('User Data', {
            'fields': (('name', 'email'), ('city', 'phone_number', 'phone_number_verified', 'referer')),
            'classes': ['collapse in']
        }),
    )
    readonly_fields = ['referer']
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
    list_display = ('name', 'email', 'is_superuser', 'group', 'action')
    list_filter = ('is_superuser', GroupNameFilter)
    search_fields = ('name', 'email')
    list_editable = ('name', 'is_superuser')

    @staticmethod
    def group(user_admin):
        return user_admin.groups.first()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(is_superuser=True) | Q(is_staff=True))


@admin.register(Group)
class GroupAdmin(GroupAdmin):
    list_display = ('name', 'count')

    @staticmethod
    def count(group):
        return group.user_set.count()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(name__in=['Admin', 'Support'])
