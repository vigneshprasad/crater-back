from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_models


class UserScore(base_models.BaseModel):
    """User score model. It stores the user's score calculated based on the user's
        profile details.

    """
    user = models.ForeignKey(
        get_user_model(),
        related_name='match_score',
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField()

    def __str__(self):
        return '{} - {}'.format(self.user, self.score)


class UserToUserMatchScore(base_models.BaseModel):
    """This model stores match score between two users."""
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
