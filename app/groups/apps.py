from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GroupsConfig(AppConfig):
    name = 'groups'
    icon_name = 'groups'
    verbose_name = _('Groups')

    def ready(self):
        # Complete this apps have signals and receivers.
        pass
