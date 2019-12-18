from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MasterClassConfig(AppConfig):
    name = 'resources.masterclasses'
    icon_name = 'videocam'
    verbose_name = _('Master Classes')
