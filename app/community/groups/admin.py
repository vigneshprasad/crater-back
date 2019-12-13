from django.contrib import admin
from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe

from community.groups.models import Group, Location, UserGroup


class GroupInline(admin.StackedInline):
    model = Group
    extra = 0


@register(Location)
class UserAdmin(ModelAdmin):
    list_display = ('name', 'groups')
    inlines = [GroupInline]
    icon_name = 'location_on'

    @staticmethod
    def groups(location):
        if not location.groups.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([group.name for group in location.groups.all()])


@register(UserGroup)
class UserGroupAdmin(ModelAdmin):
    icon_name = 'people_outline'
    list_display = ('user', 'group', 'is_approved')
    list_editable = ('is_approved',)
    list_filter = ('is_approved',)
