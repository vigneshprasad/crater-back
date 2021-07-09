from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models

from matching.validation import constants


class UserValidation(base_models.BaseModel):

    VALIDATION_RULES = (
        (constants.PHONE_PRICE_VALIDATION, constants.PHONE_PRICE_VALIDATION.title()),
        (constants.INTRODUCTION_VALIDATION, constants.INTRODUCTION_VALIDATION.title()),
        (constants.LINKEDIN_URL_VALIDATION, constants.LINKEDIN_URL_VALIDATION.title()),
        (constants.EDUCATION_LEVEL_VALIDATION, constants.EDUCATION_LEVEL_VALIDATION.title()),
    )

    VALIDATION_RESULTS = (
        (constants.VALIDATION_SCORE_HIGH_ENUM, constants.VALIDATION_SCORE_HIGH),
        (constants.VALIDATION_SCORE_LOW_ENUM, constants.VALIDATION_SCORE_LOW)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    rule = models.CharField(max_length=64, choices=VALIDATION_RULES)
    result = models.PositiveIntegerField(choices=VALIDATION_RESULTS)
    is_validated = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("User Validation")
        verbose_name_plural = _("User Validations")
        unique_together = ["user", "rule", "result"]
