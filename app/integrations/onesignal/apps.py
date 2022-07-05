from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class OnesignalConfig(AppConfig):
    name = "integrations.onesignal"
    label = "integrations.onesignal"
    icon_name = ""
    verbose_name = _("OneSignal Integrations")

    def ready(self):
        import integrations.onesignal.receivers
