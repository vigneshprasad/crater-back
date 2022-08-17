from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_models
from communications.emails import constants


class EmailTemplate(base_models.BaseModel):

    EMAIL_SERVICE_PROVIDERS = (
        (constants.EMAIL_SERVICE_PROVIDER_MAILCHIMP_ENUM, constants.EMAIL_SERVICE_PROVIDER_MAILCHIMP),
    )

    name = models.CharField(max_length=512)
    service = models.PositiveSmallIntegerField(
        default=constants.EMAIL_SERVICE_PROVIDER_MAILCHIMP_ENUM,
        choices=EMAIL_SERVICE_PROVIDERS
    )

    def __str__(self):
        return self.name


class EmailLog(base_models.BaseModel):

    email_template = models.ForeignKey(
        EmailTemplate,
        related_name="logs",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        get_user_model(),
        related_name="email_logs",
        on_delete=models.CASCADE
    )
    send_at = models.DateTimeField(auto_now_add=True)
    metadata = JSONField(null=True, blank=True)
    # Message ID from the provider's end.
    email_message_id = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=32, null=True, blank=True)

