from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MeetingConfig(AppConfig):
    name = 'resources.meetings'
    icon_name = 'meetings'
    verbose_name = _('Meetings')

    def ready(self):
        import resources.meetings.signals
        import resources.meetings.receivers
