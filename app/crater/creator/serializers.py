from django.contrib.auth import get_user_model
from rest_framework import serializers

from crater.creator import models


class UserPropertiesSerializer(serializers.ModelSerializer):

    photo = serializers.SerializerMethodField()
    introduction = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "photo",
            "name",
            "introduction",
        )

    @staticmethod
    def get_photo(user):
        # If the user has no profile. Return None here.
        if not hasattr(user, "profile"):
            return None

        return (
            user.profile.photo.url
            if user.profile.photo
            else user.profile.photo_url
        )

    @staticmethod
    def get_introduction(user):
        # If the user has no profile. Return None here.
        if not hasattr(user, "profile"):
            return None

        return user.profile.get_introduction()


class CreatorSerializer(serializers.ModelSerializer):

    # TODO(Nishant): Figure out how to update all these Method fields onto a user's profile.
    about = serializers.SerializerMethodField(read_only=True)
    photo = serializers.SerializerMethodField(read_only=True)
    photo_url = serializers.SerializerMethodField(read_only=True)
    cover_photo = serializers.SerializerMethodField(read_only=True)

    # Return serializer default community for a creator.
    default_community = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = models.Creator
        fields = (
            "id",
            "user",
            "number_of_subscribers",
            "certified",
            "follower_count",
            "type",
            "about",
            "photo",
            "photo_url",
            "cover_photo"
        )
        extra_kwargs = {
            "number_of_subscribers": {
                "read_only": True
            },
            "certified": {
                "read_only": True
            },
            "follower_count": {
                "read_only": True
            },
            "type": {
                "read_only": True
            }
        }

    @staticmethod
    def get_about(obj):
        if not obj.user.has_profile:
            return None
        return obj.user.profile.get_introduction()

    @staticmethod
    def get_photo(obj):
        if not obj.user.has_profile:
            return None
        return obj.user.profile.photo

    @staticmethod
    def get_photo_url(obj):
        if not obj.user.has_profile:
            return None
        return obj.user.profile.photo_url

    @staticmethod
    def get_cover_photo(obj):
        if not obj.user.has_profile:
            return None
        return obj.user.profile.cover

    @staticmethod
    def get_default_community(obj):
        community = models.Community.objects.filter(
            creator=obj,
            is_default=True,
            is_active=True
        ).first()

        if not community:
            return None

        return CommunitySerializer(community).data


class FollowerSerializer(serializers.ModelSerializer):

    user_properties = serializers.SerializerMethodField()

    class Meta:

        model = models.Follower
        fields = (
            "id",
            "user",
            "creator",
            "unfollowed",
            "followed_at",
            "unfollowed_at",
            "user_properties"
        )
        extra_kwargs = {
            "unfollowed": {
                "required": False
            },
            "unfollowed_at": {
                "required": False
            },
            "followed_at": {
                "required": False
            }
        }

    @staticmethod
    def get_user_properties(follower):
        """Returns user properties like name, photo etc.
            for display.

        """
        return UserPropertiesSerializer(follower.user).data


class CommunitySerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Community
        fields = (
            "id",
            "name",
            "creator",
            "is_default",
            "is_active"
        )


class CommunityMemberSerializer(serializers.ModelSerializer):

    user_properties = serializers.SerializerMethodField()

    class Meta:

        model = models.CommunityMember
        fields = (
            "id",
            "community",
            "joined_at",
            "user",
            "user_properties"
        )
        extra_kwargs = {
            "joined_at": {
                "required": False
            }
        }

    @staticmethod
    def get_user_properties(follower):
        """Returns user properties like name, photo etc.
            for display.

        """
        return UserPropertiesSerializer(follower.user).data
