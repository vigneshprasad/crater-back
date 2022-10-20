import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from base import models as base_models
from crater.auth import constants
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

    def __str__(self):
        return "{} ({})".format(self.id, self.phone_number)

    def expire(self):
        """Expire the OTP."""
        self.is_expired = True
        if not self.expired_at:
            self.expired_at = timezone.now()

        self.save()

    def is_used(self):
        """Return if the OTP is used."""
        if not (self.used and self.user):
            return False

        return True

    def can_use_otp(self):
        """Can the OTP be used to log in/signup."""
        if self.used or self.is_expired:
            return False

        return True


class PhoneOTPFailure(base_models.BaseModel):
    """Keeps track of failure of OTPs on the
        platform.

    """

    # Last successful (used) OTP on the platform
    last_successful_otp = models.ForeignKey(
        PhoneOtp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    last_successful_otp_at = models.DateTimeField(auto_now_add=True)
    # OTPs generated since last successful OTP
    generated_since_last_successful = models.PositiveIntegerField(default=0)
    # Maximum number of bearable OTPs failures.
    maximum_opt_failures_allowed = models.PositiveIntegerField(
        default=constants.MAXIMUM_FAILED_OPT_ATTEMPTS
    )

    def __str__(self):
        return "{} - {}".format(
            self.last_successful_otp.id,
            self.generated_since_last_successful
        )

    @property
    def local_last_successful_opt_at(self):
        """Return start in the local timezone."""
        return self.last_successful_otp_at.astimezone(
            pytz.timezone(settings.TIME_ZONE)
        )

    @property
    def get_display_last_successful_opt_at(self):
        return self.local_last_successful_opt_at.strftime(
            "%b. %-d, %Y, %I:%M %p"
        )
