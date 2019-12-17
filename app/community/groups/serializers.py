from rest_framework import serializers

from community.groups.models import UserRequest, Location, Group, Block, Following
from community.mixins import SetCreatorRequestDataMixin


class UserRequestSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'user'
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = UserRequest
        fields = (
            'pk',
            'user',
            'group',
            'group_name'
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            'pk',
            'name',
        )


class LocationSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = (
            'pk',
            'name',
            'groups'
        )


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
