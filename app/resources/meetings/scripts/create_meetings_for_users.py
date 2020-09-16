import csv
import datetime
import urllib

from resources.meetings import models
from users import models as user_models
from resources.meetings import services


FIELDS = [
    'Email A',
    'Email B',
    'Day(Thursday/Friday)',
    'Time Preference(24 HR)',
    'Meeting Link',
    'Introduction A',
    'Introduction B'
]


def run(
        file_url='https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_data_week_10.csv',
        dry_run=True
):
    response = urllib.request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    meeting_config = services.get_latest_active_meeting_config()

    if not meeting_config:
        print('No Active meeting')
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
        time_preference = row.get('Time Preference').strip()
        meeting_link = row.get('Meeting Link').strip()
        introduction_a = row.get('Introduction A')
        introduction_b = row.get('Introduction B')

        # Getting the users if present.
        user_a, user_b = None, None
        try:
            user_a = user_models.User.objects.get(email=email_a)
            print('User {}'.format(email_a))
            print('Introduction: {}'.format(introduction_a))
        except user_models.User.DoesNotExist:
            print('*' * 5, 'User Does Not Exist{}'.format(email_a))

        try:
            user_b = user_models.User.objects.get(email=email_b)
            print('User {}'.format(email_b))
            print('Introduction: {}'.format(introduction_b))
        except user_models.User.DoesNotExist:
            print('*' * 5, 'User Does Not Exist{}'.format(email_b))

        # Check if time slot is there and valid.
        if time_preference.count(':') == 1:
            hour, minute = time_preference.split(':')
        if time_preference.count(':') == 2:
            hour, minute, sec = time_preference.split(':')

        start_time = datetime.time(int(hour), int(minute))
        end_time = (datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(minutes=30)).time()
        # week_time_slots = all_time_slots.filter(start_time=start_time)
        # time_slot = week_time_slots.last() if day == 'Friday' else week_time_slots.first()
        if day == 'Thursday':
            date = datetime.date(2020, 9, 3)
        elif day == 'Friday':
            date = datetime.date(2020, 9, 4)
        elif day == 'Wednesday':
            date = datetime.date(2020, 9, 2)

        if not dry_run:
            time_slot, _ = models.MeetingTimeSlot.objects.get_or_create(
                date=date,
                start_time=start_time,
                end_time=end_time
            )

            print('Time Slot for Meeting:', time_slot.get_display()) \
                if time_slot else print('*' * 5, 'No Time Slot missing for meeting')

        # Check if meeting link is present.
        print('Meeting Link: {}'.format(meeting_link)) \
            if meeting_link else print('*' * 5, 'Add Meeting Link')

        if not dry_run:
            if not (user_a and user_b):
                print('*' * 5, "User's are not present")
                continue

            update_public_introduction(user_a, introduction_a)
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
    meeting, created = models.Meeting.objects.get_or_create(
        meeting_config=meeting_config,
        link=meeting_link,
        time_slot=time_slot
    )

    if created:
        for participant in participants:
            meeting.participants.add(participant)

    return meeting
