from django.contrib import admin
from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from community.groups.models import Group, Location, UserRequest


class GroupInline(admin.StackedInline):
    model = Group
    extra = 0


class UserRequestInline(admin.TabularInline):
    model = UserRequest
    extra = 0
    fields = ('pk', 'user', 'is_approved')
    readonly_fields = ('pk', 'user', 'is_approved')

    def pk(self, user_group):
        return user_group.user.pk
    pk.short_description = _('Primary key')

    def has_add_permission(self, request, obj):
        return False


@register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ('name', 'groups')
    inlines = [GroupInline]
    icon_name = 'location_on'

    @staticmethod
    def groups(location):
        if not location.groups.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([group.name for group in location.groups.all()])


@register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ('name', 'location', 'amount_of_users')
    readonly_fields = ('name', 'location')
    inlines = [UserRequestInline]
    list_filter = ('location__name',)
    search_fields = ('name',)

    @staticmethod
    def amount_of_users(group):
        return f'{group.group_users.count()}({group.group_users.filter(is_approved=True).count()})'
    amount_of_users.short_description = _('Amount of users')


@register(UserRequest)
class UserRequestAdmin(ModelAdmin):
    icon_name = 'people_outline'
    list_display = ('user', 'group', 'is_approved')
    readonly_fields = ('user', 'group')
    list_editable = ('is_approved',)
    list_filter = ('is_approved',)
    search_fields = ('user__email',)

    def has_add_permission(self, request):
        return False
