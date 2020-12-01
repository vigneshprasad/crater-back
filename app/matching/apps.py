from django.utils.translation import ugettext_lazy as _

from django.apps import AppConfig


class MatchingConfig(AppConfig):
    name = 'matching'
    icon_name = 'my_location'
    verbose_name = _('Matching')
