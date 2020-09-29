from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GoogleAppConfig(AppConfig):
    name = 'integrations.google'
    icon_name = 'local_library'
    verbose_name = _('Google Integrations')

    def ready(self):
        import integrations.google
