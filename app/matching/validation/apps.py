from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ValidationConfig(AppConfig):
    name = "matching.validation"
    verbose_name = _("Validation")
    verbose_name_plural = _("Validations")
