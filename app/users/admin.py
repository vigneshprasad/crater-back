from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe

from users.models import User


@register(User)
class MaterialUserPictureAdmin(ModelAdmin):
    icon_name = 'person'
    list_display = ('email', 'is_active', 'is_staff', 'is_superuser', 'group')
    list_editable = ['is_active']
    list_filter = ('date_joined',)

    @staticmethod
    def group(user):
        if not user.groups.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([group.name for group in user.groups.all()])
