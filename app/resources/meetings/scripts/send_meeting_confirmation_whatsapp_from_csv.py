import csv
import datetime

from users import models as user_models
from integrations.freshchat import public as freshchat_public


def run(
        file_name='/app/resources/meetings/data/meeting_confirmation_data.csv',
        dry_run=True
):
    reader = csv.DictReader(open(file_name))
    data = []

    for row in reader:
        print('Start', '-' * 80)
        row = dict(row)
        email = row.get('Email Address').strip()
        time = row.get('Meeting')
        datetime_obj = datetime.datetime.strptime(time, '%d/%m/%Y, %H:%M')

        try:
            user = user_models.User.objects.get(email=email)
            print('User {}'.format(user.email))
            print('Slot {}'.format(datetime_obj))
            obj = {
                'user': user,
                'slot': datetime_obj
            }
            data.append(obj)
        except user_models.User.DoesNotExist:
            print('User not available for {}'.format(email))
            continue

        print('End', '-' * 80)

    print('Meta', '-' * 80)
    print('Total Users: {}'.format(len(data)))

    if not dry_run and len(data) > 0:
        freshchat_public.send_meeting_confirmation_messages(data)
