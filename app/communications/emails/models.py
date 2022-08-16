from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

# Create your models here.

from base import models as base_models


class EmailTemplates(base_models.BaseModel):

    SERVICE_TYPES = (
        (0, "Mandrill"),
    )

    name = models.CharField(max_length=512)
    service = models.PositiveSmallIntegerField(default=0, choices=SERVICE_TYPES)


class EmailLogs(base_models.BaseModel):

    email_template = models.ForeignKey(
        EmailTemplates,
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
