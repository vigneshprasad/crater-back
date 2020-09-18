import csv
import datetime
from urllib import request as urllib_request

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from resources.meetings import choices
from resources.meetings import models
from tags import models as tags_models
from users import models as user_models


FIELDS = [
    "Email",
    "Time Preference (2-4, 4-6)",
    "Linkedin",
    "Interests",
    "Introduction"
]


def run(
        file_url='https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_preference.csv',
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    meeting_config = models.MeetingConfig.objects.filter(
        is_active=False
    ).last()

    if not meeting_config:
        print('No inactive meeting')
        return

    available_time_slots = meeting_config.available_time_slots.all()

    print('Meeting Config: ', meeting_config.pk)
    print('Time Slots: ', ','.join(
        [time_slot.get_display_time() for time_slot in available_time_slots]
    ))

    for row in reader:
        print('Start', '-' * 80)
        row = dict(row)
        email = row.get('Email').strip()
        time_preferences = row.get('Time Preference', '')
        linkedin_url = _validate_url_and_return(row.get('Linkedin'))
        public_introduction = row.get('Introduction')
        interests = row.get('Interests', '')
        interests = [interest.strip() for interest in interests.split(',')]

        try:
            user = user_models.User.objects.get(email=email)
            print('User {}'.format(email))
        except user_models.User.DoesNotExist:
            print('User not available for {}'.format(email))
            continue

        print('Linkedin URL: ', linkedin_url)
        print('Public Introduction: ', public_introduction)
        print('Interests: ', interests)

        if not dry_run:
            create_user_meeting_preference(
                meeting_config,
                user,
                available_time_slots,
                time_preferences=time_preferences,
                interests=interests
            )

        print('End', '-' * 80)


def create_user_meeting_preference(
        meeting_config,
        user,
        available_time_slots,
        objective=None,
        time_preferences=None,
        interests=None,
        introduction=None,
        linkedin_url=None,

):
    print('Creating the actual User Meeting Preference object')

    if not objective:
        objective = choices.OBJECTIVE_CHOICES[0][0]

    meeting_preference, _ = models.UserMeetingPreference.objects.get_or_create(
        meeting=meeting_config,
        user=user,
        objective=objective,
    )

    interests = tags_models.Interests.objects.filter(
        name__in=interests
    )
    for interest in interests or []:
        meeting_preference.interests.add(interest)

    user_time_slots = _get_user_time_preference(time_preferences, available_time_slots)
    for slot in user_time_slots or []:
        meeting_preference.time_slots.add(slot)

    print('User Meeting Preference: ', meeting_preference.pk)

    # Creating/Updating Profile.
    profile, _ = user_models.Profile.objects.get_or_create(
        user=user
    )
    if introduction:
        profile.public_introduction = introduction
    if linkedin_url:
        profile.linkedin_url = linkedin_url

    profile.save()

    return meeting_preference


def _get_user_time_preference(time_preferences, available_time_slots):
    user_time_slots = []
    if not time_preferences:
        print('No time preference for user')
        return []

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
        slots = available_time_slots.filter(
            start_time__gte=start_time,
            end_time__lte=end_time
        )
        for slot in slots:
            user_time_slots.append(slot)

    print('User Time Slots: ', ','.join(
        [user_time_slot.get_display_time() for user_time_slot in user_time_slots]
    ))
    return user_time_slots


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
