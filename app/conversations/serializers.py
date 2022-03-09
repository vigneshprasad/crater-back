import copy
import datetime

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from conversations import constants, exceptions, models, services
from integrations.dyte import public as dyte_public
from integrations.dyte import serializers as dyte_serializers
from resources.meetings import serializers as meeting_serializers
from resources.meetings import models as meeting_models
from resources.curated_articles import serializers as articles_serializer
from users import serializers as user_serializers
from community.mixins import SetCreatorRequestDataMixin
from crater.creator import serializers as creator_serializers

from utils import fields


class GroupRTMPSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.GroupRtmp
        fields = (
            "id",
            "group",
            "link",
            # "linkedin",
            # "twitter",
            # "instagram",
            # "facebook"
        )


class GroupRecordingSerializer(serializers.ModelSerializer):
    dyte_recordings_details = dyte_serializers.DyteMeetingRecordingSerializer(
        source="dyte_recordings",
        many=True,
        read_only=True
    )

    class Meta:
        model = models.GroupRecording
        fields = (
            "id",
            "group",
            "recording",
            "dyte_recordings",
            "is_published",
            "published_at",
            "dyte_recordings_details"
        )


class SuggestedTopicSerializer(serializers.ModelSerializer):
    topic = serializers.CharField(source="name")

    class Meta:
        model = models.SuggestedTopic
        fields = ("topic", "suggested_by", "is_approved", "type")
        extra_kwargs = {
            "suggested_by": {"required": False},
            "is_approved": {"required": False}
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        ref_name = "group_category"
        model = models.Category
        fields = (
            "pk",
            "name",
            "color",
            "photo",
            "order"
        )


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
    creator_detail = creator_serializers.CreatorSerializer(source="creator", read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "email",
            "name",
            "photo",
            "introduction",
            "creator_detail",
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
    categories_detail_list = CategorySerializer(source="categories", many=True, read_only=True)
    interests_detail_list = meeting_serializers.MeetingInterestSerializer(source="interests", read_only=True, many=True)
    speakers_detail_list = GroupUserSerializer(source="speakers", read_only=True, many=True)
    attendees_detail_list = GroupUserSerializer(source="attendees", read_only=True, many=True)
    host_detail = GroupUserSerializer(source="host", read_only=True)
    is_speaker = serializers.SerializerMethodField(read_only=True)
    is_past = serializers.SerializerMethodField()
    relevancy = serializers.SerializerMethodField()
    recording_details = GroupRecordingSerializer(source="recording", read_only=True)

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
            "categories_detail_list",
            "recording_details"
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
        """Returns the relevancy score of a group in
            regard to the user.

        """

        request = self.context.get("request")
        if not request:
            return 0

        user = request.user
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


class EmptyGroupWebinarSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Group
        fields = ("id", )


class GroupWebinarSerializer(serializers.ModelSerializer):
    topic_detail = TopicSerializer(source="topic", read_only=True)
    host_detail = GroupUserSerializer(source="host", read_only=True)
    # Host profile details.
    host_profile_details = user_serializers.ProfileSerializer(
        source="host.profile",
        read_only=True
    )

    topic_title = serializers.CharField(required=True, write_only=True)
    topic_image = fields.Base64FileField(file_formats=[".jpg", ".png", ".tiff", ".bmp"], allow_null=True,
                                         required=False,
                                         write_only=True)
    live_count = serializers.SerializerMethodField(read_only=True)
    rsvp = serializers.SerializerMethodField(read_only=True)

    categories_detail_list = CategorySerializer(source="categories", many=True, read_only=True)

    # TODO(Nishant): Figure out how to show is past.
    is_past = serializers.SerializerMethodField(read_only=True)
    recording_details = GroupRecordingSerializer(source="recording", read_only=True)
    speakers_detail_list = GroupUserSerializer(source="speakers", read_only=True, many=True)
    # rtmp_detail = GroupRTMPSerializer(source="rtmp", read_only=True)
    rtmp_link = serializers.CharField(required=False, write_only=True)
    series = serializers.SerializerMethodField(read_only=True, allow_null=True)

    class Meta:
        model = models.Group
        fields = (
            "id",
            "host",
            "topic",
            "topic_title",
            "topic_image",
            "description",
            "start",
            "privacy",
            "medium",
            "closed",
            "closed_at",
            "topic_detail",
            "host_detail",
            "host_profile_details",
            "type",
            "is_live",
            "live_count",
            "rsvp",
            "is_past",
            "is_featured",
            "categories",
            "categories_detail_list",
            "recording_details",
            "speakers",
            "speakers_detail_list",
            # "rtmp_detail",
            "rtmp_link",
            "series",
        )

        extra_kwargs = {
            "host": {"read_only": True},
            "privacy": {"read_only": True},
            "medium": {"read_only": True},
            "closed": {"read_only": True},
            "closed_at": {"read_only": True},
            "type": {"read_only": True},
            "is_live": {"read_only": True},
            "topic": {"read_only": True},
            "categories": {"required": True},
            "speakers": {"required": False},
        }

    @staticmethod
    def get_is_past(group):
        """Return True if the meeting was in the past."""
        if group.is_live:
            return False

        now = timezone.now() - datetime.timedelta(hours=6)
        return now >= group.start

    @staticmethod
    def get_live_count(group):
        """Return live count or return 0."""
        if not group.dyte_webinar.first():
            return 0

        return group.dyte_webinar.first().meeting_participants.filter(
            is_online=True
        ).count() or 0

    def get_rsvp(self, group):
        request = self.context.get("request")
        user = request.user

        if user.is_anonymous:
            return None
        elif group.host and group.host.uuid == user.uuid:
            return None

        if not dyte_public.get_dyte_participant_for_user_and_group(
                user=user,
                group=group
        ):
            return False

        return True

    @staticmethod
    def get_series(group):
        series = group.get_series()
        if not series:
            return None
        return series.id

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        tomorrow = timezone.now() + datetime.timedelta(hours=24)

        # Raise an exception if the user already has a group
        # at the same time.
        start = validated_data["start"]
        if services.get_groups_for_user_and_start(user, start):
            raise serializers.ValidationError(exceptions.GroupCreatedAtTheSameTime().get_error_body())
        elif start < timezone.now():
            raise serializers.ValidationError(exceptions.GroupStartDateTimeNotInFuture().get_error_body())
        elif start < tomorrow:
            raise serializers.ValidationError(exceptions.GroupStartLessThan24Hours().get_error_body())

        title = validated_data.pop("topic_title") if validated_data.get("topic_title") else None
        image = validated_data.pop("topic_image") if validated_data.get("topic_image") else None
        rtmp_link = validated_data.pop("rtmp_link") if validated_data.get("rtmp_link") else None
        speakers = validated_data.get("speakers", []) + [user]

        topic = services.get_or_create_topic(
            name=title,
            image=image,
            description=validated_data.get("description"),
            creator=user
        )

        # Create webinar once topic is created.
        webinar_data = {
            "host": user,
            "topic": topic,
            "speakers": speakers,
            "privacy": constants.GROUP_PRIVACY_PUBLIC_ENUM,
            "medium": constants.GROUP_MEDIUM_AUDIO_VIDEO_ENUM,
            "type": constants.GROUP_TYPE_WEBINAR_ENUM,
            "calculate_score": False,
            "is_published": True
        }
        validated_data.update(webinar_data)

        instance = super().create(validated_data)

        if rtmp_link:
            _ = services.create_group_rtmp(
                group=instance,
                rtmp_link=rtmp_link
            )

        return instance


class StreamListTopicSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Topic
        fields = (
            "name",
            "image",
            "description"
        )


class StreamListHostSerializer(serializers.ModelSerializer):

    photo = serializers.SerializerMethodField(read_only=True)
    introduction = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "email",
            "name",
            "photo",
            "introduction"
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


class StreamListSerializer(serializers.ModelSerializer):
    """List serializer for Streams.

    Note:
        This only returns data required over a /list calls
            for calls the stream.

    """
    topic_detail = StreamListTopicSerializer(source="topic", read_only=True)
    host_detail = StreamListHostSerializer(source="host", read_only=True)

    class Meta:
        model = models.Group
        fields = (
            "id",
            "topic_detail",
            "host_detail",
            "start"
        )


class GroupChatUserSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "name",
            "email",
            "first_name",
        )

    @staticmethod
    def get_first_name(user):
        return user.get_display_first_name()


class GroupMessageSerializer(serializers.ModelSerializer):
    sender_detail = GroupChatUserSerializer(source="sender", read_only=True)

    class Meta:
        model = models.GroupMessage
        fields = (
            "id",
            "group",
            "sender",
            "message",
            "display_name",
            "created_at",
            "sender_detail",
            "type",
            "data"
        )


class ChatReactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ChatReaction
        fields = (
            "id",
            "image",
            "name",
            "is_active",
            "file",
        )


class SeriesSerializer(serializers.ModelSerializer):
    topic_detail = TopicSerializer(source="topic", read_only=True)
    groups_detail_list = GroupWebinarSerializer(source="groups", many=True, read_only=True)
    categories_detail_list = CategorySerializer(source="categories", many=True, read_only=True)
    host_detail = GroupUserSerializer(source="host", read_only=True)

    class Meta:
        model = models.Series
        fields = (
            "id",
            "topic",
            "topic_detail",
            "groups",
            "groups_detail_list",
            "categories",
            "categories_detail_list",
            "host",
            "host_detail",
            "start",
            "created_at",
        )


class SeriesListHostSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "name"
        )


class SeriesListTopicSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Topic
        fields = (
            "name",
            "image",
            "description"
        )


class SeriesListSerializer(serializers.ModelSerializer):

    topic_detail = SeriesListTopicSerializer(source="topic", read_only=True)
    groups_detail_list = EmptyGroupWebinarSerializer(source="groups", many=True, read_only=True)
    host_detail = SeriesListHostSerializer(source="host", read_only=True)

    class Meta:
        model = models.Series
        fields = (
            "id",
            "topic_detail",
            "groups_detail_list",
            "host_detail",
            "start"
        )
