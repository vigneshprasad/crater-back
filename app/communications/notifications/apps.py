from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ConversationsConfig(AppConfig):
    name = "communications.notifications"
    verbose_name = _("Notifications")
    verbose_name_plural = _("Notifications")

    def ready(self):
        pass
