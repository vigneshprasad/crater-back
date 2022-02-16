import copy
from numpy import source
from rest_framework import serializers

from crater.auctions import constants, models
from crater.creator import serializers as creator_serializers
from base import serializers as base_serializers
from users import serializers as user_serializers


class AuctionSerializer(serializers.ModelSerializer):
    minimum_bid = serializers.SerializerMethodField(read_only=True)    
    last_bid = serializers.SerializerMethodField(read_only=True)    

    class Meta:
        model = models.Auction
        fields = (
            "id",
            "coin",
            "start",
            "end",
            "is_closed",
            "is_active",
            "base_price",
            "number_of_coins",
            "coins_sold",
            "minimum_bid",
            "last_bid"
        )
    
    @staticmethod
    def get_minimum_bid(obj):
        highest_bid = obj.bids.filter(status=constants.BID_STATUS_ACCEPTED_ENUM).order_by("-bid_price").first()
        if not highest_bid:
            return obj.base_price
        return constants.MINIMUM_BID_MULTIPLIER(highest_bid.bid_price)


    @staticmethod
    def get_last_bid(obj):
        bid = obj.bids.filter(status=constants.BID_STATUS_ACCEPTED_ENUM).order_by("-created_at").first()
        if not bid:
            return None
        return BidSerializer(bid).data


class BidSerializer(serializers.ModelSerializer):
    coin_detail = creator_serializers.CoinSerializer(source="auction.coin", read_only=True)
    status_detail = base_serializers.DisplayChoiceField(
        choices=models.Bid.BID_STATUS_CHOICES,
        read_only=True, source="status"
    )
    bidder_profile_detail = user_serializers.ProfileSerializer(source="bidder.profile", read_only=True)

    class Meta:
        model = models.Bid
        fields = (
            "id",
            "bidder",
            "auction",
            "bid_price",
            "number_of_coins",
            "status",
            "is_processed",
            "payment",
            "coin_detail",
            "amount",
            "created_at",
            "status_detail",
            "bidder_profile_detail"
        )

    def to_internal_value(self, data):
        """Initial transform data for serializer, set user as request user

        Args:
            data(dict): Request data passed to the serializer.

        """
        try:
            data = copy.deepcopy(data)
        except TypeError:
            pass

        if self.context.get("request"):
            data["bidder"] = self.context["request"].user.pk

        return super().to_internal_value(data)


class CoinPriceLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CoinPriceLog
        fields = (
            "id",
            "coin",
            "created_at",
            "price",
        )
