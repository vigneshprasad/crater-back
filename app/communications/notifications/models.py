from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_model


class Notification(base_model.BaseModel):
    name = models.CharField(max_length=256)
    content = JSONField()
    is_active = models.BooleanField(default=True)


class UserNotifications(base_model.BaseModel):
    # TODO(Nishant): Add is_read, read_time fields.
    user = models.ForeignKey(
        get_user_model(),
        related_name='notifications',
        on_delete=models.CASCADE
    )
    notification = models.ForeignKey(
        "communications.notifications.Notification",
        on_delete=models.CASCADE
    )
