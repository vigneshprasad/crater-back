from rest_framework import serializers

from users.models import User
from tags.serializers import TagSerializer


class UserTraitsSerializer(serializers.ModelSerializer):
    work_city = serializers.SerializerMethodField()
    social_auth = serializers.SerializerMethodField()
    user_tags = serializers.SerializerMethodField()
    twitter = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    user_objectives = serializers.SerializerMethodField(
        read_only=True
    )
    linkedin = serializers.CharField(
        source='profile.linkedin_url',
        read_only=True
    )

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
            'user_objectives',
            'linkedin'
        )

    @staticmethod
    def get_city(user):
        if not user.city:
            return None
        return user.city.name

    @staticmethod
    def get_social_auth(user):
        if not user.socialaccount_set.all():
            return None
        return user.socialaccount_set.first().provider

    @staticmethod
    def get_work_city(user):
        if not (user.has_profile and user.profile.work_city):
            return None
        return user.profile.work_city.name

    @staticmethod
    def get_user_tags(user):
        if not user.has_profile:
            return None
        user_tags = TagSerializer(user.profile.tags, many=True, read_only=True).data
        return ', '.join([tag['name'] for tag in user_tags])

    @staticmethod
    def get_twitter(user):
        if not user.has_profile:
            return None
        return user.profile.twitter

    @staticmethod
    def get_phone(user):
        return str(user.phone_number)

    @staticmethod
    def get_user_objectives(user):
        if not user.objectives.all():
            return None
        return ', '.join(
            [objective.name for objective in user.objectives.all()]
        )
