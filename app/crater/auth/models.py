from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

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
    # Is the OTP requested for signup
    # or login.
    signup = models.BooleanField(default=False)
    # OTP for login
    otp = models.CharField(max_length=4)

    # Marked when the OTP is used for login/signup.
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    # Marked True for an expired OTP.
    is_expired = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def expire(self):
        """Expire the OTP."""
        self.is_expired = True
        if not self.expired_at:
            self.expired_at = timezone.now()

        self.save()

    def can_use_otp(self):
        """Can the OTP be used to login/signup."""
        if self.used or self.is_expired:
            return False

        return True
