import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from resources.meetings import choices
from resources.meetings import models
from resources.meetings import signals
from tags import models as tags_models
from users import services as users_services


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


@receiver(post_save, sender=models.MeetingConfig)
def send_analytics_for_meeting_config_creation(sender, instance, created, *args, **kwargs):
    if not created:
        return

    time_slots = instance.available_time_slots.all()
    all_time_slots = []
    for time_slot in time_slots:
        slot = {
            'start_time': str(time_slot.start_time),
            'end_time': str(time_slot.end_time),
            'date': str(time_slot.date)}
        all_time_slots.append(slot)

    signals.new_meeting_config_created.send(
        sender=instance,
        user=users_services.get_admin_user(),
        title=instance.title,
        week_start_date=str(instance.week_start_date),
        week_end_date=str(instance.week_end_date),
        registration_start_date=str(instance.registration_start_date),
        registration_end_date=str(instance.registration_end_date),
        time_slots=all_time_slots
    )


@receiver(signals.create_new_meeting_preference_typeform)
def create_meeting_preference_for_typeform_user(
        sender, user, time_preferences, interests, days, objective, *args, **kwargs
):

    clean_time_preferences = []
    for time_preference in time_preferences:
        clean_time_preferences.append(_clean_time_preference(time_preference))

    meeting_config = models.MeetingConfig.objects.filter(
        is_active=False
    ).last()

    objective_value = choices.OBJECTIVE_CHOICES[0][0]
    for key, value in choices.OBJECTIVE_CHOICES:
        if value == objective:
            objective_value = objective

    start_date = meeting_config.week_start_date
    end_date = meeting_config.week_end_date

    end_date_weekday = end_date.weekday()

    dates = []
    for day in days:
        if day == 'Thursday':
            day_weekday = 3
        else:
            day_weekday = 4

        date_diff = end_date_weekday - day_weekday
        date = end_date - datetime.timedelta(days=date_diff)
        dates.append(date)

    user_time_slots = []

    for date in dates:
        for time_preference in clean_time_preferences:
            start, end = time_preference.split('-')
            start = int(start.strip()) + 12
            end = int(end.strip()) + 12
            start_time, end_time = datetime.time(start), datetime.time(end)
            time_slot, _ = models.TimeSlot.objects.get_or_create(
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            user_time_slots.append(time_slot)

    meeting_preference, _ = models.UserMeetingPreference.objects.get_or_create(
        meeting=meeting_config,
        user=user,
        objective=objective_value
    )
    interests = tags_models.Interests.objects.filter(
        name__in=interests
    )
    for interest in interests or []:
        meeting_preference.interests.add(interest)
    for slot in user_time_slots or []:
        meeting_preference.time_slots.add(slot)


REMOVE_CHARS = ['PM', 'pm', 'Pm', 'pM', 'p.m.']


def _clean_time_preference(time_preference):
    for i in REMOVE_CHARS:
        time_preference = time_preference.replace(i, '')
    return time_preference
