from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import ugettext_lazy as _


class PhoneOtp(base_models.BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        related_name="otp",
        on_delete=models.CASCADE
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone number")
    )
    otp = models.CharField(max_length=4)
    used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
