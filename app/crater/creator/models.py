from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from base import models as base_models


class Creator(base_models.BaseModel):
    """Creator profile for a user on the platform.

    Note: Only gets built when a user wants to create
        a community.

    """
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE
    )

    # Number of subscribers (off the platform)
    number_of_subscribers = models.PositiveIntegerField(null=True, blank=True)
    # Once a creator reaches a certain mark, we can mark them
    # certified.
    certified = models.BooleanField(default=False)
    type = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    # Temporary key for showcasing creators.
    order = models.PositiveIntegerField(null=True, blank=True)
    follower_count = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["follower_count"]

    def __str__(self):
        return "{}".format(self.user.__str__())


class Community(base_models.BaseModel):
    """Communities created by a creator.

    Note: All creators will have
        a default community.

    """
    name = models.CharField(
        max_length=64
    )
    creator = models.ForeignKey(
        Creator,
        related_name="communities_owned",
        on_delete=models.CASCADE,
    )
    # For every creator one community is created by default.
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{}".format(self.name)


class CommunityMember(base_models.BaseModel):
    """Members of the creator community

    Note: Right now all people following
        are part of the default community.

    """
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        get_user_model(),
        related_name="communities_joined",
        on_delete=models.CASCADE
    )
    # When the user joined the
    joined_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)


class Follower(base_models.BaseModel):
    """Followers of a creator on Crater club.

    Note: Followers will be added to the default
        community for a creator.

    """
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="following"
    )
    # When the user started following the creator.
    followed_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    # Is the creator being followed right now.
    unfollowed = models.BooleanField(default=False)
    unfollowed_at = models.DateTimeField(null=True, blank=True)


class Coin(base_models.BaseModel):
    """Coin of the creator."""
    creator = models.OneToOneField(
        Creator,
        on_delete=models.CASCADE
    )
    # Coins held by the creator at the current moment.
    coins_held = models.PositiveIntegerField()

    price = models.PositiveIntegerField()
    # Maximum coins that can be help by the creator.
    max_coins = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    # Contains all the display functionality
    # of the creator coin.
    display = JSONField(default=dict)
