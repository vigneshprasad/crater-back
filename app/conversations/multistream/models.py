from django.db import models

from base import models as base_model


class MultiStream(base_model.BaseModel):
    """
    A collection of groups known as Squad
    """
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(
        'conversations.Category',
        related_name="squads",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    streams = models.ManyToManyField(
        'conversations.Group',
        related_name="squads",
        blank=True
    )
