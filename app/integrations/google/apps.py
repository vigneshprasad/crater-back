from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GoogleAppConfig(AppConfig):
    name = 'integrations.google'
    label = 'integrations.google'
    icon_name = ''
    verbose_name = _('Google Integrations')

    def ready(self):
        import integrations.google.receivers
