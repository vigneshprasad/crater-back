from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GroupConfig(AppConfig):
    name = 'community.groups'
    icon_name = 'people_outline'
    verbose_name = _('Community Group')

    def ready(self):
        import community.groups.receivers
        import community.groups.signals