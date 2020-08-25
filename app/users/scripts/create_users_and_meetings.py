import csv
import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from resources.meetings import models as meeting_models
from users import models
from resources.meetings import services
from users.scripts.create_users_from_csv import create_user_and_profile


FIELDS = [
    # Meeting Object Fields
    'Email A',
    'Email B',
    'Day(Thursday/Friday)',
    'Time Preference(24 HR)',
    'Meeting Link',

    # User Object Fields
    'Full Name A',
    'Full Name B',
    'Interest A',
    'Interest B',
    'Objective A',
    'Objective B',
    'Tags A',
    'Tags B',
    'Phone Number A',
    'Phone Number B',
    'Linkedin A',
    'Linkedin B',
    'Introduction A',
    'Introduction B'
]


def run(
        file_name='/app/resources/meetings/data/1_on_1_meeting_data.csv',
        dry_run=True
):
    reader = csv.DictReader(open(file_name))

    meeting_config = services.get_latest_active_meeting_config()

    if not meeting_config:
        print('No inactive meeting')
        return

    all_time_slots = meeting_config.available_time_slots.all()

    print('Meeting Config: ', meeting_config.pk)
    print('Time Slots: ', ','.join(
        [time_slot.get_display_time() for time_slot in all_time_slots]
    ))

    for row in reader:
        print('Start', '-' * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email_a = row.get('Email A').strip()
        email_b = row.get('Email B').strip()
        day = row.get('Day', 'Friday').strip()
        time_preference = row.get('Time preference').strip()
        meeting_link = row.get('Meeting Link').strip()

        # User A Fields.
        full_name_a = row.get('Full Name A', '').strip()
        linkedin_url_a = _validate_url_and_return(row.get('Linkedin A'))
        phone_number_a = row.get('Phone Number A') or None
        raw_interests = row.get('Interests A', '').split(',')
        interests_a = [interest.strip() for interest in raw_interests]
        raw_objectives = row.get('Objectives A', '').split(',')
        objectives_a = [objective.strip() for objective in raw_objectives]
        raw_tags = row.get('Tags A', '').split(',')
        tags_a = [tag.strip() for tag in raw_tags]
        introduction_a = row.get('Introduction A')

        # User B Fields.
        full_name_b = row.get('Full Name A', '').strip()
        linkedin_url_b = _validate_url_and_return(row.get('Linkedin A'))
        phone_number_b = row.get('Phone Number A') or None
        raw_interests = row.get('Interests A', '').split(',')
        interests_b = [interest.strip() for interest in raw_interests]
        raw_objectives = row.get('Objectives A', '').split(',')
        objectives_b = [objective.strip() for objective in raw_objectives]
        raw_tags = row.get('Tags A', '').split(',')
        tags_b = [tag.strip() for tag in raw_tags]
        introduction_b = row.get('Introduction B')

        # Meeting Preference Fields.
        # TODO(Nishant): Handle meeting preference creation as well.
        time_preference_a = row.get('User Time Preference A')
        time_preference_b = row.get('User Time Preference B')

        # Getting the users if present.
        user_a, user_b = None, None
        profile_a, profile_b = None, None

        try:
            user_a = models.User.objects.get(email=email_a)
            print('User {}'.format(email_a))
        except models.User.DoesNotExist:
            print('Will create user: {}'.format(email_a))

        try:
            user_b = models.User.objects.get(email=email_b)
            print('\nUser {}'.format(email_b))
        except models.User.DoesNotExist:
            print('Will create user: {}'.format(email_a))

        # Check if time slot is there and valid.
        hour, minute = time_preference.split(':')
        start_time = datetime.time(hour, minute)
        week_time_slots = all_time_slots.filter(start_time=start_time)
        time_slot = week_time_slots.last() if day == 'Friday' else week_time_slots.first()
        print('Time Slot for Meeting: {}', time_slot.get_display()) \
            if time_slot else print('*' * 5, 'Time Slot missing for meeting')

        # Check if meeting link is present.
        print('Meeting Link: {}'.format(meeting_link)) \
            if meeting_link else print('*' * 5, 'Add Meeting Link')

        if not dry_run:

            if not user_a:
                user_a, profile_a = create_user_and_profile(
                    full_name=full_name_a,
                    email=email_a,
                    phone_number=phone_number_a,
                    linkedin_url=linkedin_url_a,
                    username=None,
                    interests=interests_a,
                    objectives=objectives_a,
                    source=None,
                    tags=tags_a,
                    introduction=introduction_a
                )
                print('Created User {}'.format(email_a))

            if not user_b:
                user_b, profile_b = create_user_and_profile(
                    full_name=full_name_b,
                    email=email_b,
                    phone_number=phone_number_b,
                    linkedin_url=linkedin_url_b,
                    username=None,
                    interests=interests_b,
                    objectives=objectives_b,
                    source=None,
                    tags=tags_b,
                    introduction=introduction_b
                )
                print('Created User {}'.format(email_b))

            if not profile_a:
                update_public_introduction(user_a, introduction_a)

            if not profile_b:
                update_public_introduction(user_b, introduction_b)

            meeting = create_meeting(
                meeting_config,
                meeting_link,
                time_slot,
                participants=[user_a, user_b]
            )
            print("Created Meeting for users {} & {}: {}".format(email_a, email_b, meeting.id))

        print('End', '-' * 80)


def update_public_introduction(user, introduction):
    if not hasattr(user, 'profile'):
        print("*" * 5, "Profile not there was user {}".format(user.email))
    if not introduction:
        return
    profile = user.profile
    profile.public_introduction = introduction
    profile.save()


def create_meeting(meeting_config, meeting_link, time_slot, participants):
    meeting, created = meeting_models.Meeting.objects.get_or_create(
        meeting_config=meeting_config,
        link=meeting_link,
        time_slot=time_slot
    )

    if created:
        for participant in participants:
            meeting.participants.add(participant)

    return meeting


def _validate_url_and_return(url):
    if not url:
        return None

    url = url.strip()
    try:
        validator = URLValidator()
        validator(url)
    except ValidationError:
        return None

    return url
