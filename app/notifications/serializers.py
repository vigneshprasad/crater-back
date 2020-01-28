from rest_framework import serializers

from . import models


class UserNotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserNotificationsSettings
        fields = [
            'messages',
            'post_comments',
            'post_likes',
            'new_videos_posted',
            'new_articles_posted',
            'new_events_created'
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
    author_avatar = serializers.FileField(source='notification.author_avatar', read_only=True)
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


class EmptySerializer(serializers.Serializer):
    pass
