from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ChatConfig(AppConfig):
    name = 'consumers.chat'
    icon_name = 'chat'
    verbose_name = _('Chat')

    def ready(self):
        import consumers.chat.signals
        import consumers.chat.receivers
