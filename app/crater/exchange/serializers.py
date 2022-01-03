from rest_framework import serializers

from crater.exchange import models


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction


class UserCoinHoldingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserCoinHolding
