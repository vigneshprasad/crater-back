from rest_framework import serializers
from pytz import timezone

from . import models

tz = timezone(settings.TIME_ZONE)


class UserNotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserNotificationsSettings
        fields = [
            'messages',
            'post_comments',
            'post_likes',
            'new_videos_posted',
            'new_articles_posted',
            'new_events_created',
            'new_post_created'
        ]


class PushNotificationSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(source='notification.obj_type', read_only=True)
    text = serializers.CharField(source='notification.text', read_only=True)
    author_name = serializers.CharField(source='notification.author_name', read_only=True)
    obj_pk = serializers.IntegerField(source='notification.obj_pk', read_only=True)

    class Meta:
        model = models.UserNotification
        fields = [
            'is_read',
            'pk',
            'obj_type',
            'obj_pk',
            'author_name',
            'text',
            'created'
        ]


class NotificationSerializer(PushNotificationSerializer):
    author_avatar = serializers.CharField(source='notification.author_avatar', read_only=True)
    event_date = serializers.DateField(source='notification.event.date', allow_null=True)


    class Meta:
        model = models.UserNotification
        fields = [
            'is_read',
            'pk',
            'obj_type',
            'obj_pk',
            'author_name',
            'author_avatar',
            'text',
            'created',
            'event_date'
        ]

    @staticmethod
    def get_created(comment):
        return comment.created.astimezone(tz)


class EmptySerializer(serializers.Serializer):
    pass
