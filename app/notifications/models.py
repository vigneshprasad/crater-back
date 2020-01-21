from django.db import models

from django.utils.translation import ugettext_lazy as _


class UserNotificationsSettings(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='notification_settings',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    messages = models.BooleanField(
        default=True
    )
    post_comments = models.BooleanField(
        default=True
    )
    post_likes = models.BooleanField(
        default=True
    )
    new_videos_posted = models.BooleanField(
        default=True
    )
    new_articles_posted = models.BooleanField(
        default=True
    )
    new_events_created = models.BooleanField(
        default=True
    )
