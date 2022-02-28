from rest_framework import serializers, fields

from crater.rewards import models
from crater.auctions import models as auction_models
from crater.auctions import constants as auction_constants
from crater.creator import serializers as creator_serializers


class RewardTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardType
        fields = (
            "id",
            "name",
            "is_active"
        )


class RewardSerializer(serializers.ModelSerializer):
    photo_mime_type = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.SerializerMethodField(read_only=True)
    quantity_sold = serializers.SerializerMethodField(read_only=True)
    active_auction = serializers.SerializerMethodField(read_only=True)
    creator_detail = creator_serializers.CreatorSerializer(source="creator", read_only=True)
    type_detail = RewardTypeSerializer(source="type", read_only=True)

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

        return AuctionSerializer(auction).data


class RedemptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Redemption
        fields = "__all__"


class AuctionSerializer(serializers.ModelSerializer):
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
        highest_bid = obj.bids.filter(status=auction_constants.BID_STATUS_ACCEPTED_ENUM).order_by("-bid_price").first()
        if not highest_bid:
            return obj.base_price
        return auction_constants.MINIMUM_BID_MULTIPLIER(highest_bid.bid_price)
