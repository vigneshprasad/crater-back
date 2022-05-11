from django.contrib.auth import get_user_model
from rest_framework import serializers

from crater.creator import models
from users import models as user_models
from users import serializers as user_serializers
from crater.creator import constants


class CreatorSerializer(serializers.ModelSerializer):

    profile_detail = user_serializers.ProfileSerializer(source="user.profile", read_only=True)

    # Return serializer default community for a creator.
    default_community = serializers.SerializerMethodField(read_only=True)
    is_follower = serializers.SerializerMethodField(read_only=True)
    is_subscriber = serializers.SerializerMethodField(read_only=True)

    point_of_contact_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = models.Creator
        fields = (
            "id",
            "user",
            "subscriber_count",
            "certified",
            "follower_count",
            "type",
            "order",
            "default_community",
            "profile_detail",
            "slug",
            "is_follower",
            "show_club_members",
            "video",
            "video_poster",
            "show_analytics",
            "is_subscriber",
            "point_of_contact",
            "point_of_contact_detail",
        )
        extra_kwargs = {
            "subscriber_count": {
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
            },
            "slug": {
                "read_only": True
            },
            "show_club_members": {
                "read_only": True
            },
            "show_analytics": {
                "read_only": True
            }
        }

    def get_is_follower(self, creator):
        """Returns True if the requesting user is
            following the creator.

        """
        request = self.context.get("request")
        if not request:
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False
        # If the user is the same as the creator. Return True
        if user.pk == creator.user.pk:
            return True

        return creator.followers.filter(user=user).exists()

    def get_is_subscriber(self, creator):
        """Returns True if the requesting user has
            subscribed to the creator

        """
        request = self.context.get("request")
        if not request:
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False
        # If the user is the same as the creator. Return True
        if user.pk == creator.user.pk:
            return True

        return creator.followers.filter(user=user, notify=True).exists()

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

    @staticmethod
    def get_point_of_contact_detail(obj):
        if obj.point_of_contact:
            return user_serializers.UserDetailSerializer(obj.point_of_contact).data

        try:
            default_poc_user = get_user_model().objects.get(email=constants.DEFAULT_POC_EMAIL)
        except get_user_model().DoesNotExist:
            return None

        return user_serializers.UserDetailSerializer(default_poc_user).data


class CreatorProfileListSerializer(serializers.ModelSerializer):

    photo = serializers.ImageField(read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = user_models.Profile
        fields = (
            "id",
            "name",
            "photo"
        )


class CreatorListSerializer(serializers.ModelSerializer):

    profile_detail = CreatorProfileListSerializer(source="user.profile", read_only=True)

    class Meta:
        model = models.Creator
        fields = (
            "id",
            "user",
            "slug",
            "subscriber_count",
            "profile_detail"
        )


class FollowerSerializer(serializers.ModelSerializer):

    profile_detail = user_serializers.ProfileSerializer(source="user.profile", read_only=True)

    class Meta:

        model = models.Follower
        fields = (
            "id",
            "user",
            "creator",
            "unfollowed",
            "followed_at",
            "unfollowed_at",
            "profile_detail",
            "notify",
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

    profile_detail = user_serializers.ProfileSerializer(source="user.profile", read_only=True)

    class Meta:

        model = models.CommunityMember
        fields = (
            "id",
            "community",
            "joined_at",
            "user",
            "profile_detail"
        )
        extra_kwargs = {
            "joined_at": {
                "required": False
            }
        }


class CoinSerializer(serializers.ModelSerializer):

    creator_detail = CreatorSerializer(source="creator", read_only=True)

    class Meta:

        model = models.Coin
        fields = (
            "id",
            "name",
            "is_active",
            "display",
            "creator_detail"
        )
        extra_kwargs = {
            "is_active": {
                "read_only": True
            }
        }
