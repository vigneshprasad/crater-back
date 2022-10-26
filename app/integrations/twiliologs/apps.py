from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TwiliologsConfig(AppConfig):
    name = "integrations.twiliologs"
    label = "twiliologs"
    verbose_name = _("Twilio")
    verbose_name_plural = _("Twilio")

    def ready(self):
        import integrations.twiliologs.receivers
