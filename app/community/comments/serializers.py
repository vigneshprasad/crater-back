from rest_framework import serializers
from pytz import timezone

from community.comments.models import Comment
from community.mixins import SetCreatorRequestDataMixin
from django.conf import settings

tz = timezone(settings.TIME_ZONE)


class CommentSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'creator'
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    creator_photo = serializers.ImageField(source='creator.profile.photo', read_only=True)
    creator_id = serializers.UUIDField(source='creator.pk', read_only=True)
    created = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'pk',
            'message',
            'creator_id',
            'creator_name',
            'creator_photo',
            'creator',
            'created',
            'post',
            'event'
        )
        extra_kwargs = {
            'post': {'write_only': True},
            'event': {'write_only': True},
            'creator': {'write_only': True}
        }

    @staticmethod
    def get_created(comment):
        return comment.created.astimezone(tz)
