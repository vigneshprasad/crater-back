from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from integrations.freshchat import constants
from users import models as user_models


class FreshChatUser(base_models.BaseModel):
    user = models.OneToOneField(
        user_models.User,
        related_name='freshchat_user',
        on_delete=models.CASCADE,
        verbose_name=_('FreshChat User')
    )
    freshchat_user_id = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )


class Message(base_models.BaseModel):
    # Possible message statuses from Freshchat.
    message_statuses = (
        (constants.FRESHCHAT_MESSAGE_ACCEPTED, constants.FRESHCHAT_MESSAGE_ACCEPTED),
        (constants.FRESHCHAT_MESSAGE_IN_PROGRESS, constants.FRESHCHAT_MESSAGE_IN_PROGRESS),
        (constants.FRESHCHAT_MESSAGE_SENT, constants.FRESHCHAT_MESSAGE_SENT),
        (constants.FRESHCHAT_MESSAGE_DELIVERED, constants.FRESHCHAT_MESSAGE_DELIVERED),
        (constants.FRESHCHAT_MESSAGE_FAILED, constants.FRESHCHAT_MESSAGE_FAILED)
    )

    user = models.ForeignKey(
        user_models.User,
        related_name='freshchat_messages',
        on_delete=models.CASCADE,
        verbose_name=_('FreshChat Messages')
    )
    request_id = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )
    message_id = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        choices=message_statuses
    )
    data = JSONField(
        null=True,
        blank=True
    )

    @property
    def failure_info(self):
        """Returns failure code and reason if the message sending failed."""
        if self.status not in constants.FRESHCHAT_MESSAGE_FAILURE_STATUSES:
            return {}
        if not self.data:
            return {}
        return {
            'failure_code': self.data.get('failure_code'),
            'failure_reason': self.data.get('failure_reason')
        }
