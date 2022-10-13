import datetime

from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.contrib.auth.models import Group

from crater.auth import models, private, constants
from users import models as user_models, services as user_services
from wn_analytics import constants as analytics_constants
from wn_analytics import models as analytics_models


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
            value = value.strip()

            # Check if referrer exists
            try:
                user = user_models.User.objects.get(pk=value)
            except (user_models.User.DoesNotExist, ValidationError):
                user = None

            return user

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")

        validated_data["otp"] = "1111" if (
                constants.DEBUG or phone_number in constants.TEST_PHONE_NUMBERS
        ) else private.generate_otp()
        # When a new OTP is created mark the old ones as expired.
        models.PhoneOtp.objects.filter(phone_number=phone_number).update(is_expired=True)

        # Creating a new OTP for the user.
        return super().create(validated_data)

    def update(self, instance, validated_data):

        validated_data["used"] = True
        utm_source = validated_data.pop("utm_source")
        utm_campaign = validated_data.pop("utm_campaign")
        utm_medium = validated_data.pop("utm_medium")
        referrer = validated_data.pop("referrer")
        is_new_user = validated_data.get("new_user", False)

        instance = super().update(instance, validated_data)
        user = instance.user
        hack2skill_group, _ = Group.objects.get_or_create(name=constants.HACK_2_SKILL_GROUP)

        if (utm_source or utm_campaign or referrer) and is_new_user:
            # Only create if the user is a new user.
            analytics_models.UserSource.objects.create(
                user=user,
                utm_source=utm_source,
                utm_campaign=utm_campaign,
                utm_medium=utm_medium,
                referrer=referrer
            )
            # Add to H2Skill users to hack2skill_group
            if utm_source == constants.HACK_2_SKILL_SOURCE:
                user.groups.add(hack2skill_group)

        # Add all new users joining on 15th and 16th without source
        # to hack2skill_group.
        elif is_new_user and (user.date_joined.date() in constants.HACK_2_SKILL_DATES):
            user.groups.add(hack2skill_group)

        if utm_source == analytics_constants.IGC_SOURCE and is_new_user:
            # Get profile for user.
            user = instance.user
            user.refresh_from_db()
            profile = user.profile
            # Opt out IGC users from whatsapp messages.
            profile.opt_out_of_whatsapp()
            return instance

        # If the referrer user is a creator don't create user referral.
        if referrer and not referrer.is_creator and is_new_user:
            # Create user referral.
            user_services.create_user_referral(
                new_user=user,
                referrer=referrer
            )

        return instance
