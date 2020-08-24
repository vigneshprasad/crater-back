import csv
import datetime

from resources.meetings import models
from users import models as user_models
from resources.meetings import services


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

    print('Start', '*' * 100)

    for row in reader:
        row = dict(row)

        email_a = row.get('Email A').strip()
        email_b = row.get('Email B').strip()

        day = row.get('Day', 'Friday').strip()
        time_preference = row.get('Time preference').strip()
        meeting_link = row.get('Meeting Link').strip()

        try:
            user_a = user_models.User.objects.get(email=email_a)
            print('\nUser {}'.format(email_a))
        except user_models.User.DoesNotExist:
            print('-' * 5, '\nUser Does Not Exist{}'.format(email_a))

        try:
            user_b = user_models.User.objects.get(email=email_b)
            print('\nUser {}'.format(email_b))
        except user_models.User.DoesNotExist:
            print('-' * 5, '\nUser Does Not Exist{}'.format(email_b))

        hour, minute = time_preference.split(':')
        start_time = datetime.time(hour, minute)

        week_time_slots = all_time_slots.filter(start_time=start_time)
        time_slot = week_time_slots.last() if day == 'Friday' else week_time_slots.first()

        if time_slot:
            print('Time Slot for Meeting: {}', time_slot.get_display())
        else:
            print('-' * 5, 'Time Slot missing for meeting')
        if not meeting_link:
            print('-' * 5, 'Add Meeting Link')
        else:
            print('Meeting Link: {}'.format(meeting_link))

        if not dry_run:
            meeting, created = models.Meeting.objects.get_or_create(
                meeting_config=meeting_config,
                link=meeting_link,
                time_slot=time_slot
            )
            if created:
                meeting.participants.add(user_a)
                meeting.participants.add(user_b)

            print("Created Meeting for users {} & {}: {}".format(
                email_a, email_b, meeting.id
            ))

        print('End', '*' * 100)
