from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from base import models as base_models


class Device(base_models.BaseModel):
    """All devices we have on the platform and their prices.

    Note:
        This class represent device entities related to it. Has
            nothing to do with the user.

    """
    name = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    # Price of the phone model in rupees.
    price = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("name", "model")

    def __str__(self):
        return "{} - {}".format(self.name, self.model)


class UserDevice(base_models.BaseModel):
    """User's device info with activity.

    Note:
        A user can have multiple devices at the same time
            but we will considered the latest used device
            for any user.

    """
    user = models.ForeignKey(
        "users.User",
        verbose_name=_("User"),
        related_name="user_devices",
        on_delete=models.CASCADE,
    )
    device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    # When this devices was last used.
    last_used = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        ordering = ("-last_used", )

    def __str__(self):
        return "{} - {}:{}".format(self.user.email, self.device.name, self.device.model)
