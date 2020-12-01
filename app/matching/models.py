from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models


class MatchScore(base_models.BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        related_name='match_score',
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField()
