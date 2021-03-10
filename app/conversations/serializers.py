from rest_framework import serializers
from django.contrib.auth import get_user_model

from conversations import models, services
from resources.meetings import serializers as meeting_serializers
from resources.meetings import models as meeting_models

from community.mixins import SetCreatorRequestDataMixin


class TopicSerializer(serializers.ModelSerializer):
    root = serializers.SerializerMethodField(read_only=True)

    class Meta:
        ref_name = "group_topic"
        model = models.Topic
        fields = (
            "id",
            "name",
            "image",
            "is_active",
            "parent",
            "is_approved",
            "description",
            "creator",
            "root"
        )

    @staticmethod
    def get_root(topic):
        root = services.get_root_topic(topic)
        if root is None:
            return None
        return TopicSerializer(root).data


class GroupHostSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'name',
            'photo',
        )

    @staticmethod
    def get_photo(user):
        profile = user.has_profile
        if not profile:
            return None

        return user.profile.get_photo_url()


class GroupSpeakerSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'name',
            'photo',
        )

    @staticmethod
    def get_photo(user):
        profile = user.has_profile
        if not profile:
            return None

        return user.profile.get_photo_url()


class GroupSerializer(serializers.ModelSerializer):
    topic = TopicSerializer()
    interests = meeting_serializers.MeetingInterestSerializer(many=True)
    speakers = GroupSpeakerSerializer(many=True)
    host = GroupHostSerializer()

    class Meta:
        ref_name = "group_meeting"
        model = models.Group
        fields = "__all__"


class InviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invite
        fields = "__all__"


class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Request
        fields = "__all__"


class OptinSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    topic_detail = TopicSerializer(source="topic", read_only=True)
    week_start = serializers.SerializerMethodField(read_only=True)
    interest_list = meeting_serializers.MeetingInterestSerializer(many=True, source="interests", read_only=True)
    time_slot_list = meeting_serializers.TimeSlotSerializer(many=True, source="time_slots", read_only=True)

    class Meta:
        model = meeting_models.MeetingPreference
        fields = (
            'user',
            'interests',
            'time_slots',
            'meeting',
            'topic',
            'week_start',
            'interest_list',
            'time_slot_list',
            'topic_detail',
        )

    @staticmethod
    def get_week_start(preference):
        return preference.meeting.week_start_date