from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_models


class MatchScore(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        related_name='match_score',
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField()
    # The score breakdown for the overall score i.e score from different engines.
    score_breakdown = JSONField(null=True, blank=True)
    # The weightage from different engines applied.
    score_weightages = JSONField(null=True, blank=True)
