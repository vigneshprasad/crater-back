from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FirebaseConfig(AppConfig):
    name = 'integrations.firebase'
    icon_name = 'local_library'
    verbose_name = _('Firebase')

    def ready(self):
      pass