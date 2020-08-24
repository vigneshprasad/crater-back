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
        email = row.get('Email Address').strip()
        time_preferences = row.get('Time preference', '')
        linkedin_url = _validate_url_and_return(row.get('Linkedin'))
        public_introduction = row.get('Introduction')
        interests = row.get('Wants to meet', '')
        interests = [interest.strip() for interest in interests.split(',')]

        try:
            user = user_models.User.objects.get(email=email)
            print('*'*80, '\nUser {}'.format(email))
        except user_models.User.DoesNotExist:
            print('*'*80, '\nUser not available for {}'.format(email))
            continue

        objective = choices.OBJECTIVE_CHOICES[0][0]

        interests = [interest.strip() for interest in interests.split(',')]
        interests = tags_models.Interests.objects.filter(
            name__in=interests
        )

        # Get time slots for User.
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
        print('Linkedin URL: ', linkedin_url)
        print('Public Introduction: ', public_introduction)
        print('Interests: ', '.'.join([interest.name for interest in interests]))
        print('Objective: ', objective)

        if not dry_run:
            create_user_meeting_preference(
                meeting_config,
                user,
                objective,
                time_slots=user_time_slots,
                interests=interests
            )
        print('-'*100)


def create_user_meeting_preference(
        meeting_config,
        user,
        objective,
        time_slots=None,
        interests=None,
        introduction=None,
        linkedin_url=None,

):
    print('Creating the actual User Meeting Preference object')

    meeting_preference, _ = models.UserMeetingPreference.objects.get_or_create(
        meeting=meeting_config,
        user=user,
        objective=objective,
    )

    for interest in interests or []:
        meeting_preference.interests.add(interest)

    for slot in time_slots or []:
        meeting_preference.time_slots.add(slot)

    print('User Meeting Preference: ', meeting_preference.pk)

    # Creating/Updating Profile.
    try:
        profile = user.profile
    except Exception as e:
        print(e)
        profile, _ = user_models.Profile.objects.get_or_create(
            user=user
        )

    if introduction:
        profile.public_introduction = introduction
    if linkedin_url:
        profile.linkedin_url = linkedin_url

    profile.save()


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
