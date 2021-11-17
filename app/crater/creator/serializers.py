from rest_framework import serializers

from crater.creator import models
from users import serializers as user_serializers


class CreatorSerializer(serializers.ModelSerializer):

    profile_detail = user_serializers.ProfileSerializer(source="user.profile", read_only=True)

    # Return serializer default community for a creator.
    default_community = serializers.SerializerMethodField(read_only=True)
    is_follower = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = models.Creator
        fields = (
            "id",
            "user",
            "number_of_subscribers",
            "certified",
            "follower_count",
            "type",
            "order",
            "default_community",
            "profile_detail",
            "slug",
            "is_follower"
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
            },
            "slug": {
                "read_only": True
            }
        }

    def get_is_follower(self, creator):
        """Returns True is the request user is already following the creator."""
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
            "profile_detail"
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
