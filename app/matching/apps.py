from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MatchingConfig(AppConfig):
    name = 'matching'
    icon_name = 'my_location'
    verbose_name = _('Matching')

    def ready(self):
        pass
