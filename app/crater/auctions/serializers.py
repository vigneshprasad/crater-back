import copy

from rest_framework import serializers

from base import serializers as base_serializers
from crater.auctions import constants, models
from crater.creator import serializers as creator_serializers
from crater.rewards import serializers as reward_serializers
from users import serializers as user_serializers


class RewardAuctionBaseSerializer(serializers.ModelSerializer):

    minimum_bid = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.RewardAuction
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
        """Return minimum bid price, after multiplier."""
        highest_bid = obj.bids.filter(
            status=constants.BID_STATUS_ACCEPTED_ENUM
        ).order_by("-bid_price").first()
        if not highest_bid:
            return obj.base_price

        return constants.get_amount_with_bid_multiplier(highest_bid.bid_price)


class BidSerializer(serializers.ModelSerializer):

    status_detail = base_serializers.DisplayChoiceField(
        choices=models.Bid.BID_STATUS_CHOICES,
        read_only=True,
        source="status"
    )
    bidder_profile_detail = user_serializers.ProfileSerializer(source="bidder.profile", read_only=True)
    creator_detail = creator_serializers.CreatorSerializer(source="creator", read_only=True)
    auction_detail = RewardAuctionBaseSerializer(source="auction", read_only=True)
    reward_detail = reward_serializers.RewardSerializer(source="auction.reward", read_only=True)

    class Meta:
        model = models.Bid
        fields = (
            "id",
            "creator",
            "bidder",
            "auction",
            "bid_price",
            "quantity",
            "status",
            "is_processed",
            "payment",
            "amount",
            "created_at",
            "status_detail",
            "bidder_profile_detail",
            "creator_detail",
            "auction_detail",
            "reward_detail"
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


class RewardAuctionListSerializer(RewardAuctionBaseSerializer):
    reward_detail = reward_serializers.RewardDetailWithCreatorAndTypeSerializer(source="reward", read_only=True)

    class Meta:
        model = models.RewardAuction
        fields = (
            "id",
            "reward",
            "reward_detail",
            "start",
            "end",
            "is_closed",
            "is_active",
            "base_price",
            "minimum_bid",
        )
