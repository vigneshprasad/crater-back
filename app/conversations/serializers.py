import copy
import datetime

from django.utils import timezone

from rest_framework import serializers
from django.contrib.auth import get_user_model


from conversations import constants
from conversations import exceptions
from conversations import models
from conversations import services
from resources.meetings import serializers as meeting_serializers
from resources.meetings import models as meeting_models
from resources.curated_articles import serializers as articles_serializer

from community.mixins import SetCreatorRequestDataMixin


class SuggestedTopicSerializer(serializers.ModelSerializer):

    topic = serializers.CharField(source="name")

    class Meta:
        model = models.SuggestedTopic
        fields = ("topic", "suggested_by", "is_approved", "type")
        extra_kwargs = {
            "suggested_by": {"required": False},
            "is_approved": {"required": False}
        }


class TopicSerializer(serializers.ModelSerializer):

    root = serializers.SerializerMethodField(read_only=True)
    article_detail = articles_serializer.CuratedArticleSerializer(source="article", read_only=True)

    class Meta:
        ref_name = "group_topic"
        model = models.Topic
        fields = (
            "id",
            "name",
            "image",
            "is_active",
            "article",
            "parent",
            "is_approved",
            "description",
            "creator",
            "root",
            "article_detail"
        )

    @staticmethod
    def get_root(topic):
        root = services.get_root_topic(topic)
        if root is None:
            return None
        return TopicSerializer(root).data


class GroupUserSerializer(serializers.ModelSerializer):

    photo = serializers.SerializerMethodField(read_only=True)
    introduction = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "email",
            "name",
            "photo",
            "introduction",
        )

    @staticmethod
    def get_photo(user):
        profile = user.has_profile
        if not profile:
            return None

        return user.profile.get_photo_url()

    @staticmethod
    def get_introduction(user):
        return user.profile.get_introduction() if user.has_profile else None


class GroupSerializer(serializers.ModelSerializer):

    topic_detail = TopicSerializer(source="topic", read_only=True)
    interests_detail_list = meeting_serializers.MeetingInterestSerializer(source="interests", read_only=True, many=True)
    speakers_detail_list = GroupUserSerializer(source="speakers", read_only=True, many=True)
    attendees_detail_list = GroupUserSerializer(source="attendees", read_only=True, many=True)
    host_detail = GroupUserSerializer(source="host", read_only=True)
    is_speaker = serializers.SerializerMethodField(read_only=True)
    is_past = serializers.SerializerMethodField()
    relevancy = serializers.SerializerMethodField()

    class Meta:
        ref_name = "group_meeting"
        model = models.Group
        fields = (
            "id",
            "host",
            "speakers",
            "is_speaker",
            "topic",
            "description",
            "interests",
            "start",
            "end",
            "max_speakers",
            "privacy",
            "medium",
            "closed",
            "closed_at",
            "topic_detail",
            "host_detail",
            "speakers_detail_list",
            "interests_detail_list",
            "is_past",
            "relevancy",
            "is_approved",
            "type",
            "attendees",
            "attendees_detail_list",
        )
        extra_kwargs = {
            "is_approved": {"required": False}
        }

    @staticmethod
    def get_is_past(group):
        """Return True if the meeting was in the past."""
        now = timezone.now() - datetime.timedelta(days=1)
        return now >= group.start

    def get_relevancy(self, group):
        """Returns the relevancy score of a group with
            regards to the user.

        """

        user = self.context.get("request").user
        # If group score or user score is not there return zero.
        if not (user and (group.score and user.score)):
            return 0

        if group.score >= user.score:
            return 100

        return int(group.score / user.score * 100)

    def get_is_speaker(self, group):
        """Returns True if the user is a speaker in the group."""
        request = self.context.get("request")

        # TODO(Abhishek): Remove if unnecessary
        if not (request and request.user):
            return False

        user = request.user
        if group.host == user:
            return True
        elif user in group.speakers.all():
            return True

        return False

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        # Raise an exception if the user already has a group
        # at the same time.
        start = validated_data["start"]
        if services.get_groups_for_user_and_start(user, start):
            raise exceptions.GroupCreatedAtTheSameTime()

        return super().create(validated_data)


class InviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invite
        fields = "__all__"


class RequestSerializer(serializers.ModelSerializer):
    group_detail = GroupSerializer(source="group", read_only=True)

    class Meta:
        model = models.Request
        fields = (
            "pk",
            "requester",
            "group",
            "status",
            "is_recommended",
            "group_detail",
            "participant_type"
        )

    def to_internal_value(self, data):
        """
        Initial transform data for serializer, set creator as request user
        :param data: request data
        """
        try:
            data = copy.deepcopy(data)
        except TypeError:
            pass
        if self.context.get("request"):
            data["requester"] = self.context["request"].user.pk
        return super().to_internal_value(data)


class OptinSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    topic_detail = TopicSerializer(source="topic", read_only=True)
    week_start = serializers.SerializerMethodField(read_only=True)
    interest_list = meeting_serializers.MeetingInterestSerializer(many=True, source="interests", read_only=True)
    time_slot_list = meeting_serializers.TimeSlotSerializer(many=True, source="time_slots", read_only=True)

    class Meta:
        model = meeting_models.MeetingPreference
        fields = (
            "user",
            "interests",
            "time_slots",
            "meeting",
            "topic",
            "week_start",
            "interest_list",
            "time_slot_list",
            "topic_detail",
        )

    @staticmethod
    def get_week_start(preference):
        return preference.meeting.week_start_date


class GroupWebinarSerializer(serializers.ModelSerializer):

    topic_detail = TopicSerializer(source="topic", read_only=True)
    host_detail = GroupUserSerializer(source="host", read_only=True)

    topic = serializers.CharField(required=True, write_only=True)
    image = serializers.FileField(required=False, write_only=True)
    live_count = serializers.SerializerMethodField(read_only=True)
    rsvp = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Group
        fields = (
            "id",
            "host",
            "topic",
            "image",
            "description",
            "start",
            "privacy",
            "medium",
            "closed",
            "closed_at",
            "topic_detail",
            "host_detail",
            "type",
            "is_live",
            "live_count",
            "rsvp"
        )

        extra_kwargs = {
            "host": {"read_only": True},
            "privacy": {"read_only": True},
            "medium": {"read_only": True},
            "closed": {"read_only": True},
            "closed_at": {"read_only": True},
            "type": {"read_only": True},
            "is_live": {"read_only": True}
        }

    @staticmethod
    def get_live_count(group):
        """Return live count or return 0."""
        if group.dyte_webinar.first():
            return 0

        return group.dyte_webinar.first().meeting_participants.filter(
            is_online=True
        ).count() or 0

    def get_rsvp(self, group):
        request = self.context.get("request")
        user = request.user

        if user.is_anonymous:
            return None
        elif group.host.uuid == user.uuid:
            return None

        if not services.get_dyte_meeting_participant(
                meeting_id=group.dyte_webinar.first().dyte_meeting_id,
                user_uuid=user.uuid
        ):
            return False

        return True

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        # Raise an exception if the user already has a group
        # at the same time.
        start = validated_data["start"]
        if services.get_groups_for_user_and_start(user, start):
            raise exceptions.GroupCreatedAtTheSameTime()

        if validated_data.get("image", None) is not None:
            validated_data.pop("image")

        topic = services.get_or_create_topic(
            name=validated_data.get("topic"),
            image=validated_data.get("image"),
            description=validated_data.get("description"),
            creator=user
        )

        # Create webinar once topic is created.
        webinar_data = {
            "host": user,
            "topic": topic,
            "speakers": [user],
            "privacy": constants.GROUP_PRIVACY_PUBLIC_ENUM,
            "medium": constants.GROUP_MEDIUM_AUDIO_VIDEO_ENUM,
            "type": constants.GROUP_TYPE_WEBINAR_ENUM,
            "calculate_score": False
        }
        validated_data.update(webinar_data)

        return super().create(validated_data)
