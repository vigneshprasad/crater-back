from rest_framework import serializers

from crater.sales import models
from crater.rewards import serializers as reward_serializers
from crater.creator import serializers as creator_serializers
from crater.creator import models as creator_models
from users import serializers as user_serializers

from utils import fields


class RewardSaleSerializer(serializers.ModelSerializer):
    reward_detail = reward_serializers.RewardDetailWithCreatorAndTypeSerializer(source="reward", read_only=True)

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
            "reward_detail",
            "show_in_store"
        )


class CreateSaleRewardSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=64)
    description = serializers.CharField()
    image = fields.Base64FileField(file_formats=[".jpg", ".png", ".tiff", ".bmp"], allow_null=True, required=False)

    class Meta:
        model = models.RewardSale
        fields = (
            "price",
            "quantity",
            "title",
            "description",
            "image"
        )


class RewardSaleLogSerializer(serializers.ModelSerializer):
    reward_sale_detail = RewardSaleSerializer(source="reward_sale", read_only=True)
    user_detail = user_serializers.UserDetailSerializer(source="user", read_only=True)

    class Meta:
        model = models.RewardSaleLog
        fields = (
            "id",
            "user",
            "reward_sale",
            "quantity",
            "price",
            "status",
            "payment",
            "payment_type",
            "reward_sale_detail",
            "user_detail",
        )


class RewardSaleLogSerializer(serializers.ModelSerializer):
    reward_sale_detail = RewardSaleSerializer(source="reward_sale", read_only=True)
    user_detail = user_serializers.UserDetailSerializer(source="user", read_only=True)

    class Meta:
        model = models.RewardSaleLog
        fields = (
            "id",
            "user",
            "reward_sale",
            "quantity",
            "price",
            "status",
            "payment",
            "payment_type",
            "reward_sale_detail",
            "user_detail",
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
