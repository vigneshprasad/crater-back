import os

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from utils.storage_backends import PrivateMediaStorage


class Message(TimeStampedModel):
    """
    Message instance for chat messaging users to user and user to admin
    """
    message = models.TextField()
    sender = models.ForeignKey(
        get_user_model(),
        related_name='sender_messages',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        get_user_model(),
        related_name='receiver_messages',
        on_delete=models.CASCADE,
        null=True
    )
    file = models.FileField(_('File'), upload_to='messages/%Y/%m/%d', storage=PrivateMediaStorage(), null=True)
    is_read = models.BooleanField(default=False)
    is_support = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        db_table = 'chat_messages'
        ordering = ('created',)

    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.message


class ChatStarredUser(models.Model):
    """
    Star relation between users
    """
    creator = models.ForeignKey(
        get_user_model(),
        related_name='creator_stars',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        get_user_model(),
        related_name='user_stars',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('Chat Star')
        verbose_name_plural = _('Chat Stars')
        db_table = 'chat_stars'
        unique_together = ['creator', 'user']


class Chat(models.Model):
    proxy = True


class LastSeen(TimeStampedModel):

    user = models.OneToOneField(
        'users.User',
        related_name='last_chat_activity',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('User last activity')
        verbose_name_plural = _('User last activities')
        db_table = 'last_seen'


@receiver(post_save, sender=Message)
def user_notification_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        if instance.receiver and not instance.is_support:
            send = instance.receiver.notification_settings.messages
            if send:
                from .serializers import MessageSerializer
                data = MessageSerializer(instance).data
                data['obj_type'] = 'message'
                data['obj_pk'] = data['pk']
                try:
                    username = instance.sender.name
                except Exception:
                    username = ''
                instance.receiver.send_push(
                    message=_('You have received a message from {username}').format(username=username),
                    data=data
                )
