import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from base import models as base_models
from crater.auth import constants


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
    is_signup = models.BooleanField(default=False)
    # OTP for login.
    otp = models.CharField(max_length=4)

    # Marked when the OTP is used for login/signup.
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    # Marked True for an expired OTP.
    is_expired = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)

    # Was the phone otp successful sent/delivered to the
    # phone number.
    successful = models.BooleanField(default=False)
    successful_at = models.DateTimeField(null=True, blank=True)

    def get_phone_number(self):
        return str(self.phone_number)

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

    def mark_successful(self):
        """Mark the Phone otp successful."""
        self.successful = True
        if not self.successful_at:
            self.successful_at = timezone.now()

        self.save()


class PhoneOtpMetric(base_models.BaseModel):
    """Keeps track of success metric of OTPs on the
        platform.

    """

    # Last successful (used) OTP on the platform
    last_successful = models.ForeignKey(
        PhoneOtp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Last successful OPT"
    )
    # Datetime of last successful OTP.
    last_successful_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Last OTP successful at",
        help_text="Datetime of the last successful OTP."
    )
    # OTPs generated since last successful OTP
    generated_since = models.PositiveIntegerField(
        default=0,
        verbose_name="Generated since last successful OTP",
        help_text="OTPs generated since last successful OTP."
    )
    # Maximum number of bearable OTPs failures.
    notify_at = models.PositiveIntegerField(
        default=constants.MAXIMUM_FAILED_OPT_ATTEMPTS,
        verbose_name="Notify after X failed attempts"
    )

    def __str__(self):
        return "{} - {}".format(
            self.last_successful.id if self.last_successful else "",
            self.generated_since
        )

    @property
    def local_last_successful_at(self):
        """Return last successful OTP time in the local timezone."""
        return self.last_successful_at.astimezone(pytz.timezone(settings.TIME_ZONE))

    def get_display_last_successful_at(self):
        """Returns last successful OTP in human-readable format."""
        return self.local_last_successful_at.strftime("%b. %-d, %Y, %I:%M %p")
