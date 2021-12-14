from rest_framework import serializers

from crater.auctions import models
from users import serializers as user_serializers


class AuctionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Auction
        fields = "__all__"


class BidSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Bid
        fields = "__all__"


class CoinPriceLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CoinPriceLog
        fields = "__all__"
