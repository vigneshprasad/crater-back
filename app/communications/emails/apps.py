from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EmailsConfig(AppConfig):
    name = "communications.emails"
    label = "comms_emails"
    verbose_name = _("Email")
    verbose_name_plural = _("Emails")

    def ready(self):
        import communications.emails.receivers
