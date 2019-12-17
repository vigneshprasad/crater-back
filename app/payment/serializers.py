from rest_framework import serializers
from . import models


class BaskDetailsSerializer(serializers.ModelSerializer):
    stripe_token = serializers.CharField(
        max_length=400,
        write_only=True
    )

    class Meta:
        model = models.BankDetails
        fields = [
            'membership',
            'terms_and_condition',
            'card_data',
            'stripe_token'
        ]
        readonly_fields = [
            'card_data'
        ]
