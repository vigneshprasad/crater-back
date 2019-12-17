from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from users.models import User


@register(User)
class UserAdmin(ModelAdmin):
    icon_name = 'person'
    list_display = ('name', 'email', 'group', 'date_joined', 'status', 'is_active')
    list_editable = ['is_active']
    search_fields = ('name', 'email')
    list_filter = ('groups__name', 'is_active')

    @staticmethod
    def status(user):
        if not user.is_active:
            return _('Banned')

        if user.has_profile:
            return _('Approved')
        return _('Pending')

    status.short_description = _('Status')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_superuser=False, is_staff=False)

    @staticmethod
    def group(user):
        if not user.groups.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([group.name for group in user.groups.all()])
    group.short_description = _('Roles')
