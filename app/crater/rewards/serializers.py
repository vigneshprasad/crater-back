from rest_framework import serializers

from crater.rewards import models
from users import serializers as user_serializers


class RewardTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardType


class RewardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Reward


class RedemptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Redemption
