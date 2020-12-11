from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_models


class UserScore(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        related_name='match_score',
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField()

    def __str__(self):
        return '{} - {}'.format(self.user, self.score)


class UserToUserMatchScore(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        related_name='matching_scores',
        on_delete=models.CASCADE
    )
    matched_user = models.ForeignKey(
        get_user_model(),

        on_delete=models.CASCADE
    )
    score = models.FloatField(
        null=True,
        blank=True,
        default=None
    )
    detailed_score = JSONField(blank=True, null=True)
