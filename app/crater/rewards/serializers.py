from rest_framework import serializers

from crater.rewards import models
from users import serializers as user_serializers
from crater.creator import serializers as creator_serializers


class RewardTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardType
        fields = "__all__"


class RewardSerializer(serializers.ModelSerializer):
    creator_coin_detail = creator_serializers.CoinSerializer(source="creator.coin", read_only=True)
    photo_mime_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Reward
        fields = (
            "id",
            "creator",
            "is_active",
            "name",
            "title",
            "text_color",
            "object_id",
            "type",
            "quantity",
            "remaining_quantity",
            "number_of_coins",
            "photo",
            "creator_coin_detail",
            "description",
            "photo_mime_type"
        )

    @staticmethod
    def get_photo_mime_type(reward):
        if not reward.photo:
            return None
        return reward.photo.file.obj.content_type


class RedemptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Redemption
        fields = "__all__"
