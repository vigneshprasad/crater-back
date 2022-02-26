from rest_framework import serializers

from crater.exchange import models
from crater.creator import serializers as creator_serializers
from crater.auctions import serializers as auction_serializers


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction


class UserRewardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserReward
        fields = (
            "id",
            "user",
            "reward",
            "quantity",
            "is_redeemed",
            "quantity_redeemed"
        )


class UserCoinHoldingSerializer(serializers.ModelSerializer):
    coin_detail = creator_serializers.CoinSerializer(source="coin", read_only=True)
    coin_price_log_detail = serializers.SerializerMethodField()

    class Meta:
        model = models.UserCoinHolding
        fields = (
            "id",
            "coin",
            "user",
            "number_of_coins",
            "coin_detail",
            "updated_at",
            "coin_price_log_detail",
        )

    @staticmethod
    def get_coin_price_log_detail(obj):
        log = obj.coin.log.last()
        if not log:
            return None
        return auction_serializers.CoinPriceLogSerializer(log).data
