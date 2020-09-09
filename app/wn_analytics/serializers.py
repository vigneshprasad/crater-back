from rest_framework import serializers

from users.models import User, Profile
from tags.models import CityProxy
from tags.serializers import TagSerializer


class UserTraitsSerializer(serializers.ModelSerializer):
    work_city = serializers.SerializerMethodField()
    social_auth = serializers.SerializerMethodField()
    user_tags = serializers.SerializerMethodField()
    twitter = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    user_objectives = serializers.SerializerMethodField()
    linkedin = serializers.SerializerMethodField(
        source='profile.linkedin_url',
        read_only=True,
        allow_null=True
    )
    # TODO(Nishant): Will reuse this code when Flutter app is released.
    # device_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'name',
            'email',
            'role',
            'city',
            'work_city',
            'phone',
            'email_verified',
            'phone_number_verified',
            'social_auth',
            'referer',
            'user_tags',
            'twitter',
            'source',
            'user_objectives'
            # 'device_info'
        )

    @staticmethod
    def get_city(user):
        if user.city is not None:
            return user.city.name

    @staticmethod
    def get_social_auth(user):
        if len(user.socialaccount_set.all()) > 0:
            return user.socialaccount_set.all()[0].provider
    
    @staticmethod
    def get_work_city(user):
        if user.has_profile and user.profile.work_city:
            return user.profile.work_city.name 

    @staticmethod
    def get_user_tags(user):
        if user.has_profile:
            user_tags = TagSerializer(user.profile.tags, many=True, read_only=True).data
            tags = []
            for tag in user_tags:
                tags.append(tag['name'])
            return tags
    
    @staticmethod
    def get_twitter(user):
        if user.has_profile:
            return user.profile.twitter

    @staticmethod
    def get_phone(user):
        return str(user.phone_number)

    @staticmethod
    def get_device_info(user):
        device = user.device_info.first()
        if not device:
            return {}

        return {
            'os': device.get_os_info(),
            'device': device.get_device_info(),
            'device_type': device.type
        }

    @staticmethod
    def get_user_objectives(user):
        if not user.objectives.all():
            return ''
        return {
            ','.join(objective.name for objective in user.objectives.all())
        }
