from rest_framework import serializers

from community.comments.models import Comment
from community.mixins import SetCreatorRequestDataMixin


class CommentSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'creator'
    creator_name = serializers.CharField(source='creator.name', read_only=True)

    class Meta:
        model = Comment
        fields = (
            'pk',
            'message',
            'creator_name',
            'creator',
            'post',
            'event'
        )
        extra_kwargs = {
            'post': {'write_only': True},
            'event': {'write_only': True},
            'creator': {'write_only': True}
        }
