from rest_framework import serializers

from crater.auth import models
from crater.auth import private
from crater.auth import constants
from wn_analytics import models as analytics_models
from users import models as user_models


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
            "referrer"
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

    def validate_utm_medium(self, value):
        if self.instance and value:
            return value.strip()

    def validate_referrer(self, value):
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

        utm_source = validated_data.pop("utm_source")
        utm_campaign = validated_data.pop("utm_campaign")
        utm_medium = validated_data.pop("utm_medium")
        referrer_pk = validated_data.pop("referrer")

        instance = super().update(instance, validated_data)

        if (utm_source or utm_campaign) and validated_data.get("new_user"):
            # Check if referrer exists
            try:
                referrer = user_models.User.objects.get(pk=referrer_pk)
            except user_models.User.DoesNotExist:
                referrer = None
            except Exception as e:
                referrer = None
                print(e)

            # Only create if the user is a new user.
            analytics_models.UserSource.objects.create(
                user=instance.user,
                utm_source=utm_source,
                utm_campaign=utm_campaign,
                utm_medium=utm_medium,
                referrer=referrer
            )

        return instance
