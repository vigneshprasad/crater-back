from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DyteConfig(AppConfig):
    name = "integrations.dyte"
    icon_name = "local_library"
    verbose_name = _("Dyte")

    def ready(self):
        import integrations.dyte.signals
        import integrations.dyte.receivers
