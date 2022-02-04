from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from crater.creator import services


class Creator(base_models.BaseModel):
    """Creator for a user on the platform.

    Note: Only gets built when a user wants to create
        a community.

    """
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE
    )

    # Number of subscribers (off the platform)
    subscriber_count = models.PositiveIntegerField(null=True, blank=True)
    # Once a creator reaches a certain mark, we can mark them
    # certified.
    certified = models.BooleanField(default=False)
    type = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    # Temporary key for showcasing creators.
    order = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(null=True, blank=True)
    participant_count = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)
    show_club_members = models.BooleanField(default=False)
    video = models.FileField(
        upload_to="creator/videos",
        null=True,
        blank=True
    )
    video_poster = models.ImageField(
        upload_to="creator/videos/poster/",
        null=True,
        blank=True
    )
    point_of_contact = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        related_name="point_of_contact",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-order"]

    def __str__(self):
        return "{}".format(self.user.__str__())

    def clean(self):
        if self.video and not self.video_poster:
            raise ValidationError({
                "video_poster": _("Video poster is also required with video.")
            })

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.slug:
            self.slug = services.generate_unique_slug_for_creator(self)
        return super(Creator, self).save(force_insert, force_update, using, update_fields)


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

    # This denotes if we should notify the user everytime the
    # creator goes live.
    notify = models.BooleanField(default=False)

    class Meta:
        unique_together = ["creator", "user"]

    def __str__(self):
        return f"{self.user.__str__()}"

    def delete(self, soft=True):
        # Hard deleting Follower obejcts.
        super(Follower, self).delete(soft=False)


class Coin(base_models.BaseModel):
    """Coin of the creator."""
    creator = models.OneToOneField(
        Creator,
        on_delete=models.CASCADE
    )
    # # Coins held by the creator at the current moment.
    # coins_held = models.PositiveIntegerField()
    #
    # price = models.PositiveIntegerField()
    # # Maximum coins that can be help by the creator.
    # max_coins = models.PositiveIntegerField()

    # Name of the coin.
    name = models.CharField(max_length=32, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Contains all the display functionality
    # of the creator coin.
    # TODO(Nishant): Decide fields we need for display of the coin.
    display = JSONField(default=dict)

    def __str__(self):
        return f"{self.creator.slug} - {self.id}"
