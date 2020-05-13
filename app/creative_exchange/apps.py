from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CreativeExchangeConfig(AppConfig):
    name = 'creative_exchange'
    verbose_name = _('Creative Exchange')
    icon_name = 'track_changes'
