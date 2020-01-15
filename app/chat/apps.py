from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ChatConfig(AppConfig):
    name = 'chat'
    icon_name = 'chat'
    verbose_name = _('Chat')

    def ready(self):
        import chat.signals
