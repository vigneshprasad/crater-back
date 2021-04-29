from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _


from base import models as base_model
from communications.notifications import constants


class Notification(base_model.BaseModel):
    """Notifications json from Admin."""

    OBJECT_TYPE_CHOICES = (
        (constants.OBJECT_TYPE_UPCOMING_MEETING, constants.OBJECT_TYPE_UPCOMING_MEETING.title()),
        (constants.OBJECT_TYPE_CONVERSATION, constants.OBJECT_TYPE_CONVERSATION.title()),
        (constants.OBJECT_TYPE_CREATE_CONVERSATION, constants.OBJECT_TYPE_CREATE_CONVERSATION.title()),
    )

    name = models.CharField(max_length=64)
    headings = models.CharField(max_length=64, verbose_name=_("Notification Heading"))
    contents = models.CharField(max_length=256, verbose_name=_("Notification Message"))
    small_icon = models.CharField(
        max_length=16,
        verbose_name=_("Small Notification Icon"),
        default=constants.DEFAULT_NOTIFICATION_SMALL_ICON
    )
    large_icon = models.CharField(
        max_length=64,
        verbose_name=_("Large Notification Icon"),
        null=True,
        blank=True
    )
    android_accent_color = models.CharField(
        max_length=16,
        verbose_name=_("Accent Color(Android only)"),
        default=constants.DEFAULT_NOTIFICATION_ANDROID_ACCENT_COLOR
    )
    buttons = JSONField(
        null=True,
        blank=True,
        verbose_name=_("Custom Buttons for Notifications")
    )
    obj_type = models.CharField(
        max_length=32,
        choices=OBJECT_TYPE_CHOICES,
        verbose_name=_("Client Object Type")
    )
    is_active = models.BooleanField(default=True)


class NotificationLogs(base_model.BaseModel):
    # TODO(Nishant): Add is_read, read_time fields.
    user = models.ForeignKey(
        get_user_model(),
        related_name='app_notifications',
        on_delete=models.CASCADE
    )
    notification = models.ForeignKey(
        "comms_notifications.Notification",
        on_delete=models.CASCADE
    )
    notification_json = JSONField(
        null=True,
        blank=True
    )
