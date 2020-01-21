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
