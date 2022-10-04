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
        (constants.OBJECT_TYPE_STREAM, constants.OBJECT_TYPE_STREAM.title()),
        (constants.OBJECT_TYPE_CREATOR, constants.OBJECT_TYPE_CREATOR.title())
    )

    name = models.CharField(max_length=64)
    # Headings max_length as specified in One signal.
    headings = models.CharField(
        max_length=65,
        verbose_name=_("Notification Heading"),
        help_text="65 for Android, 178 (Heading + content) for iOS."
    )
    # Content max_length as specified in One signal.
    contents = models.CharField(
        max_length=240,
        verbose_name=_("Notification Message"),
        help_text="240 for Android, 178 (Heading + content) for iOS."
    )
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

    def __str__(self):
        return self.name


class NotificationLog(base_model.BaseModel):

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
    data = JSONField(
        null=True,
        blank=True
    )

    def __str__(self):
        return "{} - {}".format(self.user, not self)
