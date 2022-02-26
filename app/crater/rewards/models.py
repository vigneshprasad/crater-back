from django.db import models
from colorfield import fields as color_fields

# Create your models here.
from base import models as base_models
from crater.rewards import constants
from resources.meetings import services as meeting_services
from conversations import services as conversation_services


class RewardType(base_models.BaseModel):
    """These are type of rewards being offered on the platform."""

    # TODO(Nishant): Create initial data with a data migration.
    name = models.CharField(max_length=32)
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Reward(base_models.BaseModel):

    # Creator who is offering this reward.
    creator = models.ForeignKey(
        "creator.Creator",
        on_delete=models.CASCADE,
        related_name="rewards"
    )
    # Name and description of the reward.
    title = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Short Title for the Reward"
    )
    name = models.CharField(max_length=128)
    text_color = color_fields.ColorField(default="#FFFFFF")
    description = models.TextField(null=True, blank=True)

    # Order in which the rewards will show up.
    order = models.PositiveIntegerField(default=0)

    # Type of rewards, 1:1, newsletter, AMA etc.
    type = models.ForeignKey(
        RewardType,
        on_delete=models.CASCADE
    )

    object_id = models.PositiveIntegerField(null=True, blank=True)

    # Display properties.
    photo = models.FileField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # TODO(Abhishek): Remove later
    quantity = models.PositiveIntegerField(default=1)
    # What quantity of the reward is left.
    remaining_quantity = models.IntegerField(null=True, blank=True)
    # Price of the Reward in creator coins.
    number_of_coins = models.PositiveIntegerField()

    class Meta:
        ordering = ["-order"]

    def get_active_auction(self):
        return self.auctions.filter(is_closed=False).last()


class Redemption(base_models.BaseModel):
    user = models.ForeignKey(
        "users.User",
        models.CASCADE
    )
    reward = models.ForeignKey(
        Reward,
        models.CASCADE
    )

    # TODO(Nishant): Object ID should be kept here rather than in Reward.
    object_id = models.PositiveIntegerField(null=True, blank=True)

    # If the redemption has expiry related to it.
    expires_at = models.DateTimeField(null=True, blank=True)

    def get_reward_object(self):
        """Returns the reward object based on the reward type."""
        if self.reward.type.name == constants.REWARD_TYPE_ONE_ON_ONE:
            return self._get_one_on_one_meeting()
        elif self.reward.type.name == constants.REWARD_TYPE_AMA:
            return self._get_ama()
        elif self.reward.type.name == constants.REWARD_TYPE_GROUP_CALL:
            return self._get_group()

    def _get_one_on_one_meeting(self):
        return meeting_services.get_meeting_for_id(self.object_id)

    def _get_ama(self):
        return conversation_services.get_ama_for_id(self.object_id)

    def _get_group(self):
        return conversation_services.get_group_for_id(self.object_id)
