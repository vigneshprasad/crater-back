from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models


class UserValidation(base_models.BaseModel):

    VALIDATION_RULES = (
        ("phone_price_validation", "Phone Price Verification"),
        ("introduction_validation", "Phone Price Verification"),
        ("linkedin_url_validation", "Phone Price Verification"),
        ("education_level_validation", "Phone Price Verification"),
    )

    VALIDATION_RESULTS = (
        (1, "Score Too High"),
        (2, "Score Too Low")
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    rule = models.CharField(choices=VALIDATION_RULES)
    result = models.PositiveIntegerField(choices=VALIDATION_RESULTS)

    class Meta:
        verbose_name = _("User Validation")
        verbose_name_plural = _("User Validations")
        unique_together = ["user", "rule", "result"]
