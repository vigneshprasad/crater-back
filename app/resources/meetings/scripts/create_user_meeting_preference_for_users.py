import csv
import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from resources.meetings import choices
from resources.meetings import models
from tags import models as tags_models
from users import models as user_models


def run(
        file_name='/app/resources/meetings/data/1_on_1_meeting_data.csv',
        dry_run=True
):

    reader = csv.DictReader(open(file_name))

    meeting_config = models.MeetingConfig.objects.filter(
        is_active=False
    ).last()

    if not meeting_config:
        print('No inactive meeting')
        return

    time_slots = meeting_config.available_time_slots.all()

    print('Meeting Config: ', meeting_config.pk)
    print('Time Slots: ', ','.join(
        [time_slot.get_display_time() for time_slot in time_slots]
    ))

    for row in reader:
        row = dict(row)
        email = row['Email Address']
        email = email.strip()
        time_preferences = row['Time preference']
        linkedin = row['Linkedin']
        public_introduction = row['Introduction']
        interests = row['Wants to meet']

        try:
            user = user_models.User.objects.get(email=email)
            print('*'*80, '\nUser {}'.format(email))
        except user_models.User.DoesNotExist:
            print('*'*80, '\nUser not available for {}'.format(email))
            continue

        linkedin_url = _validate_url_and_return(linkedin)
        print('Linkedin URL: ', linkedin_url)
        print('Public Introduction: ', public_introduction)
        if not dry_run:
            profile = user.profile
            profile.public_introduction = public_introduction
            profile.linkedin_url = linkedin_url
            profile.save()

        interests = [interest.strip() for interest in interests.split(',')]
        interests = tags_models.Interests.objects.filter(
            name__in=interests
        )
        print('Interests: ', '.'.join([interest.name for interest in interests]))
        user_time_slots = []
        if time_preferences:
            time_preferences = _clean_time_preference(time_preferences)

            if ',' in time_preferences:
                time_preferences = time_preferences.split(',')

            if not isinstance(time_preferences, list):
                time_preferences = [time_preferences]

            for time_preference in time_preferences:
                start, end = time_preference.split('-')
                start = int(start.strip()) + 12
                end = int(end.strip()) + 12
                start_time, end_time = datetime.time(start), datetime.time(end)
                slots = time_slots.filter(
                    start_time__gte=start_time,
                    end_time__lte=end_time
                )
                for slot in slots:
                    user_time_slots.append(slot)

            print('User Time Slots: ', ','.join(
                [user_time_slot.get_display_time() for user_time_slot in user_time_slots]
            ))

        objective = choices.OBJECTIVE_CHOICES[0][0]
        print('Objective: ', objective)

        if not dry_run:

            print('Create the actual User Meeting Preference object')

            meeting_preference = models.UserMeetingPreference(
                meeting=meeting_config,
                user=user,
                objective=objective,
            )
            meeting_preference.save()

            for interest in interests:
                meeting_preference.interests.add(interest)

            for slot in user_time_slots:
                meeting_preference.time_slots.add(slot)

            print('User Meeting Preference: ', meeting_preference.pk)

        print('-'*100)


REMOVE_CHARS = ['PM', 'pm', 'Pm', 'pM']


def _clean_time_preference(time_preference):
    for i in REMOVE_CHARS:
        time_preference = time_preference.replace(i, '')
    return time_preference


def _validate_url_and_return(url):
    url = url.strip()
    try:
        validator = URLValidator()
        validator(url)
    except ValidationError:
        return None
    return url
