from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AgoraConfig(AppConfig):
    name = "integrations.agora"
    label = "agora"
    icon_name = "agora"
    verbose_name = _("̄Agora")

    def ready(self):
        # Complete this apps have signals and receivers.
        pass
