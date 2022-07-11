from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TokensConfig(AppConfig):
    name = "tokens"
    icon_name = ""
    verbose_name = _("Crater Tokens")

    def ready(self):
        import tokens.receivers
