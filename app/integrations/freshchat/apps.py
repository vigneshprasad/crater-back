from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FreshChatConfig(AppConfig):
    name = 'integrations.freshchat'
    icon_name = 'local_library'
    verbose_name = _('Fresh Chat')

    def ready(self):
        import integrations.freshchat.receivers
