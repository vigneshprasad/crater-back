from rest_framework import serializers

from crater.sales import models

from crater.rewards import serializers as reward_serializers


class RewardSaleSerializer(serializers.ModelSerializer):
    reward_detail = reward_serializers.RewardBaseSerializer(source="reward", read_only=True)

    class Meta:
        model = models.RewardSale
        fields = (
            "id",
            "price",
            "quantity",
            "quantity_sold",
            "is_active",
            "reward",
            "reward_detail"
        )


class RewardSaleLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardSaleLog
        fields = "__all__"
