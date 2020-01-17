from rest_framework import serializers

from . import models


class BankDetailsSerializer(serializers.ModelSerializer):
    stripe_token = serializers.CharField(
        max_length=400,
        write_only=True,
        required=False,
        allow_null=True
    )
    remember_card = serializers.BooleanField(
        default=False,
        write_only=True
    )

    class Meta:
        model = models.BankDetails
        fields = [
            'membership',
            'terms_and_condition',
            'card_data',
            'stripe_token',
            'remember_card'
        ]
        read_only_fields = [
            'card_data'
        ]
