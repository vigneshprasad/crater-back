from django.conf import settings
from rest_framework import serializers


class TopStreamsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    rsvp_count = serializers.IntegerField(read_only=True)
    messages_count = serializers.IntegerField(read_only=True)
    start = serializers.DateTimeField(read_only=True)
    topic_title = serializers.StringRelatedField(read_only=True)
    topic_image = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_topic_image(instance):
        image = instance.get("topic_image")
        if not image:
            return None
        return f"{settings.MEDIA_URL}{image}"


class ComparativeRankingSerializer(serializers.Serializer):
    pk = serializers.UUIDField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    name = serializers.StringRelatedField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    stream_id = serializers.IntegerField(read_only=True)
    stream_topic = serializers.StringRelatedField(read_only=True)

    @staticmethod
    def get_image(instance):
        image = instance.get("image")
        if not image:
            return None
        return f"{settings.MEDIA_URL}{image}"
