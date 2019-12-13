from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EventConfig(AppConfig):
    name = 'resources.events'
    icon_name = 'assignment'
    verbose_name = _('Event')

    def ready(self):
        import resources.events.signals
