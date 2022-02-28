from django.db import models
from django.contrib.auth import get_user_model
from base.models import BaseModel
from django.contrib.postgres.fields import JSONField


class TrackLog(BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='track_log'
    )
    event = models.CharField(max_length=120)
    properties = JSONField()

    def __str__(self):
        return f"{self.user.name} ({self.event})"


class IdentifyLog(BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='identify_log'
    )
    traits = JSONField()

    def __str__(self):
        return f"{self.user.name}"


class UserSource(BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='user_source'
    )
    utm_source = models.CharField(max_length=120, null=True, blank=True)
    utm_campaign = models.CharField(max_length=120, null=True, blank=True)
    utm_medium = models.CharField(max_length=120, null=True, blank=True)
    referrer = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.name} ({self.utm_source}) ({self.utm_campaign})"
