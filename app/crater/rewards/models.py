from django.db import models

# Create your models here.
from base import models as base_models
from crater.rewards import constants
from resources.meetings import services as meeting_services
from conversations import services as conversation_services


class RewardTypes(base_models.BaseModel):
    """These are type of rewards being offered on the platform."""

    # TODO(Nishant): Create initial data with a data migration.
    name = models.CharField()
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)


class Reward(base_models.BaseModel):

    # Creator who is offering this reward.
    creator = models.ForeignKey(
        "creator.Creator",
        on_delete=models.CASCADE
    )
    # Price of the Reward in creator coins.
    number_of_coins = models.PositiveIntegerField()

    # Type of rewards, 1:1, newsletter, AMA etc.
    type = models.ForeignKey(
        RewardTypes,
        on_delete=models.CASCADE
    )
    # Related object ID based on the rewards type.
    object_id = models.PositiveIntegerField()

    # Display properties.
    photo = models.FileField(null=True, blank=True)

    def get_rewards_object(self):
        """Returns the reward object based on the reward type."""

        if self.type.name == constants.REWARD_TYPE_ONE_ON_ONE:
            return self._get_one_on_one_meeting()
        elif self.type.name == constants.REWARD_TYPE_AMA:
            return self._get_ama()
        elif self.type.name == constants.REWARD_TYPE_GROUP_CALL:
            return self._get_group()

    def _get_one_on_one_meeting(self):
        return meeting_services.get_meeting_for_id(self.object_id)

    def _get_ama(self):
        return conversation_services.get_ama_for_id(self.object_id)

    def _get_group(self):
        return conversation_services.get_group_for_id(self.object_id)


class Redemption(base_models.BaseModel):
    user = models.ForeignKey(
        "users.User",
        models.CASCADE
    )
    reward = models.ForeignKey(
        Reward,
        models.CASCADE
    )
    # If the redemption has expiry related to it.
    expires_at = models.DateTimeField(null=True, blank=True)
