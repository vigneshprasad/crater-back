from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class LocationsConfig(AppConfig):
    name = 'locations'
    icon_name = 'my_location'
    verbose_name = _('Locations')
