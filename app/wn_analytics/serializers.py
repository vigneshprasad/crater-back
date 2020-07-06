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
            'twitter'
        )

    @staticmethod
    def get_city(user):
        if user.city != None:
            return user.city.name

    @staticmethod
    def get_social_auth(user):
        if len(user.socialaccount_set.all()) > 0:
            return user.socialaccount_set.all()[0].provider
    
    @staticmethod
    def get_work_city(user):
        if user.has_profile:
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