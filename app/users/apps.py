from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UserConfig(AppConfig):
    name = 'users'
    icon_name = 'person'
    verbose_name = _('User')
