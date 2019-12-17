from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _


class GroupNameFilter(SimpleListFilter):
    title = _('Group')
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return (
            ('admin', _('Admin')),
            ('support', _('Support')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'admin':
            return queryset.filter(groups__name='Admin')
        if self.value() == 'support':
            return queryset.filter(groups__name='Support')
