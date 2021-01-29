from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GroupMeetingsConfig(AppConfig):
    name = "group_meetings"
    label = "group_meetings"
    icon_name = "group_meetings"
    verbose_name = _("Groups")

    def ready(self):
        # Complete this apps have signals and receivers.
        pass
