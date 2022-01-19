from rest_framework import serializers

from crater.gateways.stripe_payments import models


class PaymentIntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PaymentIntent
        fields = "__all__"
