from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ConversationsConfig(AppConfig):
    name = 'conversations'
    icon_name = 'people_outline'
    verbose_name = _('Conversation')
    verbose_name_plural = _('Conversations')

    def ready(self):
        import conversations.receivers
