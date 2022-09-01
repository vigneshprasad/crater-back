from rest_framework import serializers

from crater.sales import models
from crater.rewards import models as reward_models
from crater.rewards import serializers as reward_serializers
from crater.creator import serializers as creator_serializers
from crater.creator import models as creator_models


class RewardSaleBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RewardSale
        fields = (
            "id",
            "payment_type",
            "price",
            "quantity",
            "quantity_sold",
            "is_active",
            "reward"
        )


class RewardSaleSerializer(serializers.ModelSerializer):
    reward_detail = reward_serializers.RewardBaseSerializer(source="reward", read_only=True)

    class Meta:
        model = models.RewardSale
        fields = (
            "id",
            "payment_type",
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


class RewardDetailWithRewardSaleSerializer(serializers.ModelSerializer):
    creator_detail = creator_serializers.CreatorProfileListSerializer(source="creator", read_only=True)
    reward_sale_details = RewardSaleBaseSerializer(source="sale", read_only=True, many=True)

    class Meta:
        model = reward_models.Reward
        fields = (
            "id",
            "creator",
            "title",
            "description",
            "photo",
            "is_active",
            "creator_detail",
            "reward_sale_details"
        )


class RewardSellerDetailSerializer(serializers.ModelSerializer):
    profile_detail = creator_serializers.CreatorProfileListSerializer(source="user.profile", read_only=True)
    is_subscriber = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = creator_models.Creator
        fields = (
            "id",
            "user",
            "is_subscriber",
            "profile_detail"
        )

    def get_is_subscriber(self, creator):
        """Returns True if the requesting user has
            subscribed to the creator

        """
        request = self.context.get("request")
        if not request:
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False

        # If the user is the same as the creator. Return True
        if user.pk == creator.user.pk:
            return True

        return creator.followers.filter(user=user, notify=True).exists()
