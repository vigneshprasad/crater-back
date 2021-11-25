from rest_framework import serializers

from crater.auctions import models
from users import serializers as user_serializers


class AuctionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Auction


class BidSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Bid


class CoinPriceLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CoinPriceLog
