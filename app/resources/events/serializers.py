from rest_framework import serializers

from community.comments.serializers import CommentSerializer
from community.mixins import SetCreatorRequestDataMixin
from resources.events.models import Event, RSVPD


class EventSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    latest_comments = serializers.SerializerMethodField()
    rsvpd = serializers.SerializerMethodField()
    timezone = serializers.CharField(read_only=True)

    class Meta:
        model = Event
        fields = (
            'pk',
            'title',
            'text',
            'picture',
            'date',
            'start',
            'end',
            'is_free',
            'is_rsvp',
            'location',
            'capacity',
            'state',
            'timezone',
            'comments',
            'latest_comments',
            'rsvpd'
        )

    def get_rsvpd(self, event):
        return event.rsvpds.filter(user=self.context['request'].user).exists()

    @staticmethod
    def get_comments(event):
        return event.event_comments.count()

    @staticmethod
    def get_latest_comments(event):
        return CommentSerializer(event.event_comments.all()[:2], many=True).data


class RSVPDSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):

    class Meta:
        model = RSVPD
        fields = (
            'event',
            'user'
        )
        extra_kwargs = {
            'creator': {'write_only': True}
        }
