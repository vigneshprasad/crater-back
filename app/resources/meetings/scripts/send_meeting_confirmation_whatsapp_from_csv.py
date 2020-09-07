import datetime

from users import models as user_models
from integrations.freshchat import public as freshchat_public


def run(
        list_users=[],
        dry_run=True
):
    data = []

    for obj in list_users:
        print('Start', '-' * 80)
        email = obj["email"].strip()
        time = obj["meeting"]
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
