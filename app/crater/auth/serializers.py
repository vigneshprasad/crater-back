from rest_framework import serializers

from crater.auth import models
from crater.auth import private
from crater.auth import constants
from wn_analytics.models import UserSource


class PhoneOtpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="phone_number", required=False)
    utm_source = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    utm_campaign = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:

        model = models.PhoneOtp
        fields = (
            "username",
            "otp",
            "utm_source",
            "utm_campaign",
            "used",
            "is_expired"
        )
        extra_kwargs = {
            "otp": {
                "required": False,
                "allow_null": True
            },
            "used": {
                "required": False,
                "allow_null": True
            },
            "is_expired": {
                "required": False,
                "allow_null": True
            },
        }

    def validate_otp(self, value):
        # Only validate on update.
        if not self.instance:
            return True

        phone_otp = self.instance
        if phone_otp.is_expired or phone_otp.used:
            raise serializers.ValidationError("OTP provided has expired. Please generate new OTP.")

        return value

    def validate_utm_source(self, value):
        if self.instance and value:
            return value.strip()

    def validate_utm_campaign(self, value):
        if self.instance and value:
            return value.strip()

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")

        validated_data["otp"] = "1111" if (constants.DEBUG or phone_number in constants.TEST_PHONE_NUMBERS) else private.generate_otp()
        # When a new OTP is created mark the old ones as expired.
        models.PhoneOtp.objects.filter(phone_number=phone_number).update(is_expired=True)

        # Creating a new OTP for the user.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["used"] = True
        utm_source = validated_data.pop("utm_source") if validated_data.get("utm_source") else None
        utm_campaign = validated_data.pop("utm_campaign") if validated_data.get("utm_campaign") else None

        instance = super().update(instance, validated_data)

        if utm_source and utm_campaign and validated_data.get("new_user"):
            UserSource.objects.create(
                user=instance.user,
                utm_source=utm_source,
                utm_campaign=utm_campaign
            )

        return instance
