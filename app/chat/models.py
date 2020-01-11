from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


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
    is_superuser = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        db_table = 'chat_messages'
        ordering = ('-created',)
