from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from integrations.freshchat import constants
from users import models as user_models


class FreshChatUser(base_models.BaseModel):
    user = models.OneToOneField(
        user_models.User,
        related_name="freshchat_user",
        on_delete=models.CASCADE,
        verbose_name=_("FreshChat User")
    )
    freshchat_user_id = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )


class Message(base_models.BaseModel):
    # Possible message statuses from Freshchat.
    FRESHCHAT_MESSAGE_STATUS = (
        (constants.FRESHCHAT_MESSAGE_ACCEPTED, constants.FRESHCHAT_MESSAGE_ACCEPTED),
        (constants.FRESHCHAT_MESSAGE_IN_PROGRESS, constants.FRESHCHAT_MESSAGE_IN_PROGRESS),
        (constants.FRESHCHAT_MESSAGE_SENT, constants.FRESHCHAT_MESSAGE_SENT),
        (constants.FRESHCHAT_MESSAGE_DELIVERED, constants.FRESHCHAT_MESSAGE_DELIVERED),
        (constants.FRESHCHAT_MESSAGE_FAILED, constants.FRESHCHAT_MESSAGE_FAILED)
    )

    user = models.ForeignKey(
        user_models.User,
        related_name="freshchat_messages",
        on_delete=models.CASCADE,
        verbose_name=_("User")
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
        choices=FRESHCHAT_MESSAGE_STATUS
    )
    data = JSONField(
        null=True,
        blank=True
    )

    @property
    def template_name(self):
        """Return template name of the message sent to Freshchat."""
        response_data = self.data
        if not response_data:
            return None

        message_template_data = response_data.get("data").get("message_template") if \
            response_data.get("data") else None

        if not message_template_data:
            return None

        template_name = message_template_data.get("template_name")

        return template_name

    @property
    def template_data(self):
        """Return template data used to send the Freshchat message."""
        response_data = self.data
        if not response_data:
            return None

        message_template_data = response_data.get("data").get("message_template") if \
            response_data.get("data") else None

        if not message_template_data:
            return None

        template_data = message_template_data.get("template_data")

        return template_data

    @property
    def failure_info(self):
        """Returns failure code and reason if the message sending failed."""
        if self.status not in constants.FRESHCHAT_MESSAGE_FAILURE_STATUSES:
            return None

        if not self.data:
            return None

        return {
            "failure_code": self.data.get("failure_code"),
            "failure_reason": self.data.get("failure_reason")
        }
