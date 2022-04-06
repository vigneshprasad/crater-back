from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

# Create your models here.
from base import models as base_models


class Leaderboard(base_models.BaseModel):

    name = models.CharField(max_length=256)
    title = models.CharField(max_length=512)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to="leaderboard/",
        null=True,
        blank=True
    )
    rules = models.TextField(null=True, blank=True)
    # Allowed categories for the challenge.
    categories = models.ManyToManyField(
        "conversations.Category"
    )
    type = models.CharField(max_length=16)
    start = models.DateTimeField()
    end = models.DateTimeField()
    # Creators that are part of the leaderboard.
    creators = models.ManyToManyField(
        get_user_model()
    )
    is_active = models.BooleanField(default=True)
    last_calculated_at = models.DateTimeField(
        null=True,
        blank=True
    )


class UserLeaderboard(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        related_name="user_leaderboards",
        on_delete=models.CASCADE
    )
    leaderboard = models.ForeignKey(
        Leaderboard,
        related_name="user_leaderboards",
        on_delete=models.CASCADE
    )
    rank = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_minutes = models.DecimalField(default=0)
    last_calculated_at = models.DateTimeField(
        null=True,
        blank=True
    )
