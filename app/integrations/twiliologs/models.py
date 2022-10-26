from django.db import models

from base import models as base_models


class SMSLog(base_models.BaseModel):
    """SMS log for message sent by Twilio."""

    phone_otp = models.OneToOneField(
        "crater_auth.PhoneOtp",
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=32)
    sid = models.CharField(max_length=128)
    error_code = models.CharField(
        max_length=16,
        null=True,
        blank=True
    )
    error_message = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return "{} -{}".format(self.phone_otp, self.status)
