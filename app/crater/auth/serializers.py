from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from crater.auth import models, private
from users import models as user_models, services as user_services
from wn_analytics import public as analytics_public


class PhoneOtpSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="phone_number", required=False)
    utm_source = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    utm_campaign = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    utm_medium = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    referrer = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:

        model = models.PhoneOtp
        fields = (
            "username",
            "otp",
            "utm_source",
            "utm_campaign",
            "utm_medium",
            "used",
            "is_expired",
            "referrer",
            "is_signup"
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
            "is_signup": {
                "required": False,
                "allow_null": True
            }
        }

    def validate_otp(self, value):
        # Only validate on update.
        if not self.instance:
            return True

        phone_otp = self.instance
        # If the OTP can't be used, return a validation error.
        if not phone_otp.can_use_otp():
            raise serializers.ValidationError(
                "OTP provided has expired. Please generate new OTP."
            )

        return value

    def validate_utm_source(self, value):
        if not (self.instance and value):
            return

        return value.strip()

    def validate_utm_campaign(self, value):
        if not (self.instance and value):
            return

        return value.strip()

    def validate_utm_medium(self, value):
        if not (self.instance and value):
            return

        return value.strip()

    def validate_referrer(self, value):
        """Validates if the referrer is present
            in the signup request.

        """
        if not (self.instance and value):
            return

        value = value.strip()
        # Check if referrer exists
        try:
            user = user_models.User.objects.get(pk=value)
        except (user_models.User.DoesNotExist, ValidationError):
            user = None

        return user

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")
        validated_data["otp"] = private.generate_otp(phone_number)
        # When a new OTP is created mark the old unused ones as expired.
        unused_otps = models.PhoneOtp.objects.filter(
            phone_number=phone_number,
            used=False,
            is_expired=False
        )
        unused_otps.update(is_expired=True, expired_at=timezone.now())

        # Creating a new OTP for the user.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["used"] = True
        validated_data["used_at"] = timezone.now()
        utm_source = validated_data.pop("utm_source")
        utm_campaign = validated_data.pop("utm_campaign")
        utm_medium = validated_data.pop("utm_medium")
        referrer = validated_data.pop("referrer")
        is_new_user = validated_data.get("new_user", False)
        instance = super().update(instance, validated_data)

        # If it's a login, return from here.
        if not is_new_user:
            return instance

        user = instance.user
        # Create referral and source for user.
        analytics_public.create_user_source(
            user=user,
            utm_source=utm_source,
            utm_campaign=utm_campaign,
            utm_medium=utm_medium,
            referrer=referrer
        )
        user_services.create_user_referral(
            new_user=user,
            referrer=referrer
        )

        return instance
