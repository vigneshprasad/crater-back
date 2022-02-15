from rest_framework import serializers

from conversations import models as conversations_models


class TopStreamsSerializer(serializers.ModelSerializer):
    rsvp_count = serializers.IntegerField(read_only=True)
    messages_count = serializers.IntegerField(read_only=True)
    topic_title = serializers.CharField(read_only=True)
    topic_image = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = conversations_models.Group
        fields = (
            "id",
            "topic_title",
            "topic_image",
            "start",
            "rsvp_count",
            "messages_count",
        )
