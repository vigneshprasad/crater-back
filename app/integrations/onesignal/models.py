from django.db import models

from base import models as base_models
from users import models as user_models


class OneSignalDevice(base_models.BaseModel):

    os_id = models.CharField(max_length=128)
    user = models.ForeignKey(
        user_models.User,
        related_name="os_devices",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    def delete(self, soft=True):
        super(OneSignalDevice, self).delete(soft=False)

    class Meta:
        unique_together = ("user", "os_id")

    def __str__(self):
        return "{} - {}".format(self.user, self.os_id)
