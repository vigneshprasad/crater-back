from rest_framework import serializers

from tokens import models


class TokenDataPerDaySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TokenDataPerDay
        fields = "__all__"


class TokenTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TokenTransaction
        fields = "__all__"


class UserTokenLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserTokenLog
        fields = "__all__"
