from rest_framework import serializers

from crater.auth import models
from crater.auth import private

from freelance import settings


class PhoneOtpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="phone_number", required=False)

    class Meta:

        model = models.PhoneOtp
        fields = (
            "username",
            "otp",
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

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")

        if settings.DEBUG:
            validated_data["otp"] = "1111"
        else:
            validated_data["otp"] = private.generate_otp()

        # When a new OTP is created mark the old ones as expired.
        models.PhoneOtp.objects.filter(phone_number=phone_number).update(is_expired=True)

        # Creating a new OTP for the user.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["used"] = True
        return super().update(instance, validated_data)
