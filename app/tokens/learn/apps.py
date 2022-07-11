from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class LearnConfig(AppConfig):
    name = "learn"
    icon_name = ""
    verbose_name = _("Learn Tokens")

    def ready(self):
        # import tokens.learn.receivers
        pass
