from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models
from leaderboard import constants


class DurationType(base_models.BaseModel):
    """Duration Type models."""
    name = models.PositiveIntegerField(
        choices=constants.LEADERBOARD_DURATION_CHOICES,
        unique=True
    )

    def __str__(self):
        duration_type_map = dict(constants.LEADERBOARD_DURATION_CHOICES)
        return duration_type_map[self.name]


class Challenge(base_models.BaseModel):
    """Model for a challenge, contains on the display
        properties for the challenge.

    """

    name = models.CharField(max_length=256)

    # Display properties for the Challenge.
    title = models.CharField(max_length=512)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to="leaderboard/",
        null=True,
        blank=True
    )

    # Allowed categories for the challenge.
    categories = models.ManyToManyField("conversations.Category")

    # Duration of the leaderboard. Based on the duration type.
    start = models.DateTimeField()
    end = models.DateTimeField()

    # What durations are allowed for the challenge.
    duration_types = models.ManyToManyField(DurationType)
    # Challenge participants.
    participants = models.ManyToManyField(
        get_user_model(),
        related_name="challenges",
        blank=True
    )

    # Rules for the challenge.
    rules = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.id, self.title)

    def get_active_leaderboards(self):
        """Return active leaderboards for Challenges."""
        return self.leaderboards.filter(is_active=True)


class Leaderboard(base_models.BaseModel):

    challenge = models.ForeignKey(
        Challenge,
        related_name="leaderboards",
        on_delete=models.CASCADE
    )

    # Duration of the leaderboard. Based on the duration type.
    start = models.DateTimeField()
    end = models.DateTimeField()

    # Creators that are part of the leaderboard.
    duration_type = models.ForeignKey(
        DurationType,
        related_name="leaderboards",
        on_delete=models.PROTECT
    )

    # All participants of the leaderboard.
    participants = models.ManyToManyField(
        get_user_model(),
        related_name="leaderboards",
        blank=True
    )
    is_active = models.BooleanField(default=True)

    # Denotes when the leaderboard was last calculated.
    last_calculated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # class Meta:
    #     unique_together = ["challenge", "duration_type", "is_active"]

    def __str__(self):
        return "{} - {} - {}".format(self.id, self.challenge.title, self.duration_type.__str__())

    def get_active_user_leaderboards(self):
        """Return active user leaderboard for the Leaderboard."""
        return self.user_leaderboards.filter(is_active=True)


class UserLeaderboard(base_models.BaseModel):

    # User who is part of the leaderboard.
    user = models.ForeignKey(
        get_user_model(),
        related_name="leaderboard",
        on_delete=models.CASCADE
    )
    leaderboard = models.ForeignKey(
        Leaderboard,
        related_name="user_leaderboards",
        on_delete=models.CASCADE
    )

    # Not being used right now.
    rank = models.IntegerField(null=True, blank=True)

    # Total minutes attendees spent on the stream of the user.
    total_minutes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Denotes if the user is part of the leaderboard.
    is_active = models.BooleanField(default=True)
    last_calculated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return "{} ()".format(self.user, self.leaderboard)
