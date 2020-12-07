import datetime

from rest_framework import serializers

from resources.meetings import models
from resources.meetings import services

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
            'objective': latest_user_preference.objective,
            'interests': latest_user_preference.interests.values_list('pk', flat=True),
            'time_slots': latest_user_preference.time_slots.values_list('pk', flat=True)
        }
        return user_preference


class UserMeetingPreferenceSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):

    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'number_of_meetings',
            'objective',
            'objectives',
            'interests',
            'time_slots'
        )


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


#TODO: Need to deprecate this and handle on mobile with one serializer
class PastUserMeetingPreferenceSerializer(serializers.ModelSerializer):
    objectives = MeetingObjectiveSerializer(many=True)
    interests = MeetingInterestSerializer(many=True)

    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'number_of_meetings',
            'objective',
            'objectives',
            'interests',
            'time_slots'
        )


class PublicMeetingPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MeetingPreference
        fields = (
            'pk',
            'user',
            'meeting',
            'number_of_meetings',
            'objective',
            'objectives',
            'interests',
            'time_slots'
        )


class MeetingSerializer(serializers.ModelSerializer):
    is_past = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
        fields = (
            'pk',
            'config',
            'participants',
            'link',
            'time_slot',
            'start',
            'end',
            'is_canceled',
            'is_past',
            'start',
            'end',
        )

    @staticmethod
    def get_is_past(meeting):
        now = datetime.datetime.now()
        time_slot = datetime.datetime.combine(
            meeting.time_slot.date,
            meeting.time_slot.end_time
        )
        if time_slot >= now:
            return False
        return True

    @staticmethod
    def get_participants(meeting):
        return services.get_user_meeting_info(meeting)


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


class MeetingRSVPSerializer(serializers.ModelSerializer):
    meeting = MeetingSerializer()

    class Meta:
        model = models.MeetingRSVP
        fields = (
            'pk',
            'meeting',
            'participant',
            'status',
        )