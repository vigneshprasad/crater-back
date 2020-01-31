from rest_framework import serializers

from . import models


# google_verifier = GooglePlayVerifier(
#     settings.GOOGLE_BUNDLE_ID,
#     settings.GOOGLE_SERVICE_ACCOUNT_KEY_FILE,
# )
#
# apple_validator = AppStoreValidator(settings.APPLE_BUNDLE_ID, auto_retry_wrong_env_request=False)


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


class TransactionSerializer(serializers.ModelSerializer):
    order_name = serializers.CharField(source='order.title', allow_null=True, read_only=True)

    class Meta:
        model = models.Transaction
        fields = [
            'pk',
            'order_name',
            'kind',
            'amount',
            'created',
            'status',
        ]


class TransactionStatisticSerializer(serializers.Serializer):
    received_sum = serializers.IntegerField()
    paid_sum = serializers.IntegerField()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subscription
        fields = [
            'pk',
            'date_start',
            'date_end',
            'is_active',
            'google_receipt',
            'apple_receipt',
            'is_trial',
        ]
        read_only_fields = [
            'is_active',
            'is_trial'
        ]
    #
    # @staticmethod
    # def validate_google_receipt(receipt):
    #     """
    #         Accepts receipt, validates in Google.
    #         """
    #     purchase_token = receipt['purchaseToken']
    #     product_sku = receipt['productId']
    #
    #     try:
    #         result = google_verifier.verify_with_result(
    #             purchase_token,
    #             product_sku,
    #             is_subscription=True
    #         )
    #         raw_response = result.raw_response
    #         if result.is_canceled or result.is_expired:
    #             raise serializers.ValidationError(
    #                 _('Purchase validation failed')
    #             )
    #     except errors.GoogleError as exc:
    #         raise serializers.ValidationError(
    #             _('Purchase validation failed')
    #         )
    #     return receipt
    #
    # @staticmethod
    # def validate_apple_receipt(receipt):
    #     try:
    #         exclude_old_transactions = False  # if True, include only the latest renewal transaction
    #         validation_result = apple_validator.validate(
    #             receipt,
    #             'optional-shared-secret',
    #             exclude_old_transactions=exclude_old_transactions
    #         )
    #         print(validation_result)
    #     except InAppPyValidationError as ex:
    #         # handle validation error
    #         response_from_apple = ex.raw_response  # contains actual response from AppStore service.
    #         pass
