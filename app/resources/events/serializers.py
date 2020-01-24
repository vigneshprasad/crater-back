from rest_framework import serializers

from community.comments.serializers import CommentSerializer
from community.mixins import SetCreatorRequestDataMixin
from resources.events.models import Event, RSVPD


class EventSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    latest_comments = serializers.SerializerMethodField()
    is_participate = serializers.SerializerMethodField()
    count_of_participants = serializers.SerializerMethodField()
    location_name = serializers.CharField(source='location.name')

    class Meta:
        model = Event
        fields = (
            'pk',
            'title',
            'address',
            'text',
            'picture',
            'date',
            'start',
            'end',
            'is_free',
            'is_rsvp_required',
            'location',
            'location_name',
            'capacity',
            'state',
            'comments',
            'latest_comments',
            'is_participate',
            'count_of_participants',
        )

    def get_is_participate(self, event):
        if 'request' in self.context:
            return event.participants.filter(user=self.context['request'].user).exists()

    @staticmethod
    def get_count_of_participants(event):
        return event.participants.count()

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
            'user': {'write_only': True}
        }
