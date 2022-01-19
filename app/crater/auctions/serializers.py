import copy
from rest_framework import serializers

from crater.auctions import models
from crater.creator import serializers as creator_serializers
from users import serializers as user_serializers


class AuctionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Auction
        fields = "__all__"


class BidSerializer(serializers.ModelSerializer):
    coin_detail = creator_serializers.CoinSerializer(source="auction.coin", read_only=True)

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
            "amount"
        )

    def to_internal_value(self, data):
        """
        Initial transform data for serializer, set user as request user
        :param data: request data
        """
        try:
            data = copy.deepcopy(data)
        except TypeError:
            pass
        if self.context.get('request'):
            data["bidder"] = self.context['request'].user.pk
        return super().to_internal_value(data)


class CoinPriceLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CoinPriceLog
        fields = "__all__"
