from rest_framework import serializers

from crater.sales import models


class RewardSaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardSale
        fields = "__all__"


class RewardSaleLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RewardSaleLog
        fields = "__all__"
