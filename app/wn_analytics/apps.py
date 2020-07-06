from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class WNAnalyticsConfig(AppConfig):
    name = 'wn_analytics'
    verbose_name = _('Analytics')

    def ready(self):
        import wn_analytics.receivers

