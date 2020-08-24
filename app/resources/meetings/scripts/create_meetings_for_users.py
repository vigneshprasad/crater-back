import csv
import datetime

from resources.meetings import models
from users import models as user_models
from resources.meetings import services

FIELDS = ['Email A', 'Email B', 'Day(Thursday/Friday)', 'Time Preference(24 HR)', 'Meeting Link']


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

        # Getting the users if present.
        user_a, user_b = None, None
        try:
            user_a = user_models.User.objects.get(email=email_a)
            print('User {}'.format(email_a))
        except user_models.User.DoesNotExist:
            print('*' * 5, 'User Does Not Exist{}'.format(email_a))

        try:
            user_b = user_models.User.objects.get(email=email_b)
            print('\nUser {}'.format(email_b))
        except user_models.User.DoesNotExist:
            print('*' * 5, '\nUser Does Not Exist{}'.format(email_b))

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

            if not user_a and user_b:
                print('*' * 5, "User's are not present")
                continue

            meeting = create_meeting(
                meeting_config,
                meeting_link,
                time_slot,
                participants=[user_a, user_b]
            )

            print("Created Meeting for users {} & {}: {}".format(email_a, email_b, meeting.id))

        print('End', '-' * 80)


def create_meeting(meeting_config, meeting_link, time_slot, participants):
    meeting, created = models.Meeting.objects.get_or_create(
        meeting_config=meeting_config,
        link=meeting_link,
        time_slot=time_slot
    )

    if created:
        for participant in participants:
            meeting.participants.add(participant)

    return meeting
