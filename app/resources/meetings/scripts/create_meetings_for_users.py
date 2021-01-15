import csv
import datetime
from urllib import request as urllib_request

from resources.meetings import models
from users import models as user_models
from resources.meetings import services
from integrations.google.public import create_calendar_event_for_meeting


FIELDS = [
    'Email A',
    'Email B',
    'Meeting Time (%d/%m%/%y %H:%M)',
    'Introduction A',
    'Introduction B'
]


def run(
        file_url='https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_data.csv',
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    meeting_config = services.get_current_week_meeting_config()

    if not meeting_config:
        print('No Active Meeting Config.')
        return

    print('Meeting Config: ', meeting_config.pk)

    for row in reader:
        print('Start', '-' * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email_a = row.get('Email A').strip()
        email_b = row.get('Email B').strip()
        meeting_time = row.get('Meeting Time').strip()
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

        # Meeting Time Populations
        start = datetime.datetime.strptime(meeting_time, '%d/%m/%y %H:%M')
        end = start + datetime.timedelta(minutes=30)

        print("Start: {}".format(start))
        print("End: {}".format(end))

        if not dry_run:
            if not (user_a and user_b):
                print('*' * 5, "User's are not present")
                continue

            update_public_introduction(user_a, introduction_a)
            update_public_introduction(user_b, introduction_b)

            meeting = create_meeting(
                meeting_config=meeting_config,
                start=start,
                end=end,
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


def create_meeting(meeting_config, participants, start, end):
    meeting = models.Meeting.objects.create(
        config=meeting_config,
        time_slot=services.get_or_create_time_slot(start, end),
        start=start,
        end=end
    )

    for participant in participants:
        meeting.participants.add(participant)

    meeting_link = create_calendar_event_for_meeting(meeting)

    # Check if meeting link is present.
    print('Meeting Link: {}'.format(meeting_link)) \
        if meeting_link else print('*' * 5, 'Add Meeting Link')

    meeting.link = meeting_link
    meeting.save()

    return meeting
