from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SuperProConfig(AppConfig):
    name = 'integrations.superpro'
    icon_name = 'local_library'
    verbose_name = _('Super Pro')

    def ready(self):
        pass
