from django.db.models.signals import post_save
from django.dispatch import receiver

from resources.meetings import models
from resources.meetings import signals


@receiver(post_save, sender=models.UserMeetingPreference)
def send_analytics_for_user_meeting_preference(sender, instance, created, *args, **kwargs):
    time_slots = instance.time_slots.all()
    all_time_slots = []
    for time_slot in time_slots:
        slot = {
            'start_time': str(time_slot.start_time),
            'end_time': str(time_slot.end_time),
            'date': str(time_slot.date)}
        all_time_slots.append(slot)

    print({'user': instance.user,
           'meeting': instance.meeting.pk,
           'created': created,
           'week_start_date': str(instance.meeting.week_start_date),
           'week_end_date': str(instance.meeting.week_end_date),
           'number_of_meetings': instance.number_of_meetings,
           'interests': [interest.name for interest in instance.interests.all()],
           'objective': instance.objective,
           'time_slots': all_time_slots})

    signals.registered_for_meeting.send(
        sender=instance,
        user=instance.user,
        meeting=instance.meeting.pk,
        created=created,
        week_start_date=str(instance.meeting.week_start_date),
        week_end_date=str(instance.meeting.week_end_date),
        number_of_meetings=instance.number_of_meetings,
        interests=[interest.name for interest in instance.interests.all()],
        objective=instance.objective,
        time_slots=all_time_slots
    )
