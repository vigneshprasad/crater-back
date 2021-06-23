from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DevicesAppConfig(AppConfig):
    name = "devices"
    verbose_name = _("Devices")

    def ready(self):
        from devices import receivers
        from devices import signals
