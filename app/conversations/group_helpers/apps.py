from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GroupHelpersConfig(AppConfig):

    name = "conversations.group_helpers"
    label = "group_helpers"
    verbose_name = _("Group Helpers")
    verbose_name_plural = _("Group Helpers")

    def ready(self):
        pass
