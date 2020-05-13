from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DashboardConfig(AppConfig):
    name = 'dashboard'
    icon_name = 'dashboard'
    verbose_name = _(' Dashboard')  # space for admin ordering purposes
