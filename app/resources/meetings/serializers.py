import datetime

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from resources.meetings import models
from resources.meetings import services
from resources.meetings import choices

from community.mixins import SetCreatorRequestDataMixin


class ConfigPublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Config
        fields = (
            'pk',
            'title',
            'week_start_date',
            'week_end_date',
            'is_registration_open',
            'is_active'
        )


class MeetingConfigSerializer(serializers.ModelSerializer):
    available_time_slots = serializers.SerializerMethodField()
    objectives = serializers.SerializerMethodField()
    interests = serializers.SerializerMethodField()
    user_preferences = serializers.SerializerMethodField()

    class Meta:
        model = models.Config
        fields = (
            'pk',
            'title',
            'week_start_date',
            'week_end_date',
            'is_registration_open',
            'is_active',
            'available_time_slots',
            'objectives',
            'interests',
            'user_preferences'
        )

    @staticmethod
    def get_available_time_slots(meeting):
        return services.get_meeting_config_time_slots(meeting)

    @staticmethod
    def get_objectives(meeting):
        return services.get_objectives_list()

    @staticmethod
    def get_interests(meeting):
        return services.get_interest_list()

    def get_user_preferences(self, meeting):
        user = self.context['request'].user
        latest_user_preference = meeting.user_preferences.filter(user=user).last()
        if not latest_user_preference:
            return {}
        user_preference = {
            'pk': latest_user_preference.pk,
            'number_of_meetings': latest_user_preference.number_of_meetings,
            'objectives': latest_user_preference.objectives.values_list('pk', flat=True),
            'interests': latest_user_preference.interests.values_list('pk', flat=True),
            'time_slots': latest_user_preference.time_slots.values_list('pk', flat=True)
        }
        return user_preference


class MeetingObjectiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Objective
        fields = (
            'pk',
            'name',
            'icon',
            'type',
        )


class MeetingInterestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Interest
        fields = (
            'pk',
            'name',
            'icon',
        )


class PostUserMeetingPreferenceSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'number_of_meetings',
            'number_of_meetings_per_month',
            'objectives',
            'interests',
            'time_slots'
        )


class UserMeetingPreferenceSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    objectives = MeetingObjectiveSerializer(many=True)
    interests = MeetingInterestSerializer(many=True)

    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'number_of_meetings',
            'number_of_meetings_per_month',
            'objectives',
            'interests',
            'time_slots'
        )


class PublicMeetingPreferenceSerializer(serializers.ModelSerializer):
    looking_for = serializers.SerializerMethodField()
    looking_to = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    interests_display = serializers.SerializerMethodField()
    time_slots_display = serializers.SerializerMethodField()

    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'looking_for',
            'looking_to',
            'user_email',
            'interests_display',
            'time_slots_display'
        )

    @staticmethod
    def get_user_email(meeting_preference):
        return meeting_preference.user.email

    @staticmethod
    def get_looking_for(meeting_preference):
        looking_for_objectives = meeting_preference.objectives.all().filter(
            type=choices.OBJECTIVE_TYPES[0][0]
        )
        if not looking_for_objectives:
            return ''
        return ','.join([objective.name for objective in looking_for_objectives])

    @staticmethod
    def get_looking_to(meeting_preference):
        looking_to_objectives = meeting_preference.objectives.all().filter(
            type=choices.OBJECTIVE_TYPES[1][0]
        )
        if not looking_to_objectives:
            return ''
        return ','.join([objective.name for objective in looking_to_objectives])

    @staticmethod
    def get_interests_display(meeting_preference):
        interests = meeting_preference.interests.all()
        return ','.join([interest.name for interest in interests])

    @staticmethod
    def get_time_slots_display(meeting_preference):
        time_slots = meeting_preference.time_slots.all()
        return ','.join([time_slot.get_display() for time_slot in time_slots])


class MeetingUserSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    introduction = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'photo',
            'name',
            'introduction',
        )

    @staticmethod
    def get_photo(user):
        if not hasattr(user, 'profile'):
            return None
        return user.profile.photo.url if user.profile.photo else user.profile.photo_url

    @staticmethod
    def get_introduction(user):
        if not hasattr(user, 'profile'):
            return None
        return user.profile.get_introduction()


class MeetingRSVPSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MeetingRSVP
        fields = (
            'pk',
            'meeting',
            'participant',
            'status',
        )


class MeetingSerializer(serializers.ModelSerializer):
    is_past = serializers.SerializerMethodField(read_only=True)
    participants = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
        fields = [
            'pk',
            'config',
            'participants',
            'link',
            'start',
            'end',
            'is_canceled',
            'is_past',
            'status',
        ]

    @staticmethod
    def get_is_past(meeting):
        now = timezone.now()
        if meeting.end >= now:
            return False
        return True

    @staticmethod
    def get_participants(meeting):
        return services.get_meeting_participant_with_rsvp(meeting)


class PublicMeetingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Meeting
        fields = [
            'pk',
            'config',
            'participants',
            'link',
            'start',
            'end',
            'status',
        ]


class MeetingConfigV2Serializer(serializers.ModelSerializer):
    available_time_slots = serializers.SerializerMethodField()

    class Meta:
        model = models.Config
        fields = (
            'pk',
            'title',
            'week_start_date',
            'week_end_date',
            'is_registration_open',
            'is_active',
            'available_time_slots',
        )

    @staticmethod
    def get_available_time_slots(meeting):
        return services.get_meeting_config_time_slots(meeting)


class RescheduleRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RescheduleRequest
        fields = '__all__'


class PostRescheduleRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RescheduleRequest
        fields = (
            'id',
            'old_meeting',
            'requested_by',
            'time_slots'
        )

    def create(self, validated_data):
        """Handling create for RescheduleRequest object.

        Note:
            Update validated_data to have approver.

        """
        old_meeting = validated_data["old_meeting"]
        approver = old_meeting.participants.all().exclude(
            pk=validated_data["requested_by"].pk
        ).first()
        validated_data["approver"] = approver
        return super(PostRescheduleRequestSerializer, self).create(validated_data=validated_data)
