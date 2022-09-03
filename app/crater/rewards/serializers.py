from rest_framework import serializers

from crater.auctions import models as auction_models
from crater.auctions import constants as auction_constants
from crater.creator import serializers as creator_serializers
from crater.rewards import models
from utils import fields


class RewardTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardType
        fields = (
            "id",
            "name",
            "is_active"
        )


class RewardBaseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Reward
        fields = (
            "id",
            "creator",
            "title",
            "name",
            "description",
            "photo",
            "is_active",
        )


class RewardSerializer(serializers.ModelSerializer):
    photo_mime_type = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.SerializerMethodField(read_only=True)
    quantity_sold = serializers.SerializerMethodField(read_only=True)
    active_auction = serializers.SerializerMethodField(read_only=True)
    creator_detail = creator_serializers.CreatorSerializer(source="creator", read_only=True)
    type_detail = RewardTypeSerializer(source="type", read_only=True)
    photo = fields.Base64FileField(file_formats=[".jpg", ".png", ".tiff", ".bmp"], allow_null=True, required=False)

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
            "photo",
            "description",
            "photo_mime_type",
            "quantity",
            "quantity_sold",
            "active_auction",
            "creator_detail",
            "type_detail",
            "card_background"
        )

    @staticmethod
    def get_photo_mime_type(reward):
        if not reward.photo:
            return None
        return reward.photo.file.obj.content_type

    @staticmethod
    def get_quantity(reward):
        auction = reward.get_active_auction()
        if not auction:
            return 0

        return auction.quantity

    @staticmethod
    def get_quantity_sold(reward):
        auction = reward.get_active_auction()
        if not auction:
            return 0

        return auction.quantity_sold

    @staticmethod
    def get_active_auction(reward):
        auction = reward.get_active_auction()
        if not auction:
            return None

        return SubRewardAuctionSerializer(auction).data


class RedemptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Redemption
        fields = "__all__"


class SubRewardAuctionSerializer(serializers.ModelSerializer):
    minimum_bid = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = auction_models.RewardAuction
        fields = (
            "id",
            "reward",
            "start",
            "end",
            "is_closed",
            "is_active",
            "base_price",
            "minimum_bid",
        )

    @staticmethod
    def get_minimum_bid(obj):
        """Returns minimum price for bid, after multiplier."""
        highest_bid = obj.bids.filter(
            status=auction_constants.BID_STATUS_ACCEPTED_ENUM
        ).order_by("-bid_price").first()
        if not highest_bid:
            return obj.base_price

        return auction_constants.get_amount_with_bid_multiplier(highest_bid.bid_price)


class RewardDetailWithCreatorAndTypeSerializer(serializers.ModelSerializer):
    creator_detail = creator_serializers.CreatorProfileListSerializer(source="creator", read_only=True)
    type_detail = RewardTypeSerializer(source="type", read_only=True)

    class Meta:
        model = models.Reward
        fields = (
            "id",
            "creator",
            "name",
            "title",
            "type",
            "creator_detail",
            "type_detail",
        )
