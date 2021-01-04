from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_model


class VideoCall(base_model.BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        related_name='superpro_video_calls',
        on_delete=models.CASCADE
    )
    video_call_id = models.CharField(max_length=512)
    video_call_uri = models.URLField(max_length=512)
