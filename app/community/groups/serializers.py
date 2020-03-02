from rest_framework import serializers

from community.groups.models import UserRequest, Location, Group, Block, Following
from community.mixins import SetCreatorRequestDataMixin


class GroupSerializer(serializers.ModelSerializer):
    is_my = serializers.SerializerMethodField()
    is_requested = serializers.SerializerMethodField()
    location_name = serializers.CharField(source='location.name')
    location_pk = serializers.CharField(source='location.pk', read_only=True)

    class Meta:
        model = Group
        fields = (
            'pk',
            'name',
            'is_my',
            'is_requested',
            'cover',
            'icon',
            'location_name',
            'location_pk'
        )

    def get_is_my(self, group):
        return self.context['request'].user.user_groups.filter(group=group, is_approved=True).exists()

    def get_is_requested(self, group):
        return self.context['request'].user.user_groups.filter(group=group, is_approved=False).exists()


class LocationSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = (
            'pk',
            'name',
            'icon',
            'groups'
        )


class UserRequestSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'user'
    group_data = GroupSerializer(source='group', read_only=True)

    class Meta:
        model = UserRequest
        fields = (
            'pk',
            'user',
            'group',
            'group_data',
        )
        extra_kwargs = {
            'group': {'write_only': True},
        }


class BlockSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'blocker'

    class Meta:
        model = Block
        fields = (
            'pk',
            'blocked',
            'blocker'
        )


class FollowSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'follower'

    class Meta:
        model = Following
        fields = (
            'pk',
            'followed',
            'follower'
        )
