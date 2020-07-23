from rest_framework import serializers

from resources.meetings import models
from resources.meetings import services


class MeetingSerializer(serializers.ModelSerializer):
    available_time_slots = serializers.SerializerMethodField()
    objectives = serializers.SerializerMethodField()
    interests = serializers.SerializerMethodField()
    user_preferences = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
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
        all_slots = meeting.available_time_slots.all()
        print(all_slots, '*'*80)
        available_slots = {}
        for slot in all_slots:
            date_str = str(slot.date)
            if not available_slots.get(date_str):
                available_slots[date_str] = []
            available_slots[date_str].append({
                'pk': slot.pk,
                'start': slot.start_time,
                'end': slot.end_time
            })
        return available_slots

    @staticmethod
    def get_objectives(meeting):
        return services.get_objectives_list()

    @staticmethod
    def get_interests(meeting):
        return []

    def get_user_preferences(self, meeting):
        user = self.context['request'].user
        latest_user_preference = meeting.user_preferences.filter(user=user).last()
        if not latest_user_preference:
            return []
        user_preference = {
            'number_of_meetings': latest_user_preference.number_of_meetings,
            'objective': latest_user_preference.objective,
            'interests': latest_user_preference.interests.values_list('pk'),
            'slots': latest_user_preference.time_slots.values_list('pk')
        }
        return [user_preference]
