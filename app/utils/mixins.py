from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class ViewActionMixin:
    edit_icon = 'edit'
    list_action_text = ''
    list_display_links = ('action',)

    @classmethod
    def action(cls, obj):
        return mark_safe(f'{cls.list_action_text}<i class="material-icons medium-icon">{cls.edit_icon}</i>')

    action.short_description = _('Action')
