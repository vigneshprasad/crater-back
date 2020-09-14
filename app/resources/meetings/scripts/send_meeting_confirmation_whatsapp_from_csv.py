import csv
import datetime
import urllib

from users import models as user_models
from integrations.freshchat import freshchat_service, constants


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_confirmation_whatsapp.csv",
        dry_run=True
):
    data = []

    response = urllib.request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print('Start', '-' * 80)
        email = row["email"].strip()
        time = row["meeting"]
        datetime_obj = datetime.datetime.strptime(time, '%d/%m/%Y %H:%M')

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
        _send_meeting_confirmation_messages(data)


def _send_meeting_confirmation_messages(user_timing_list):
    """Send whatsapp message to user for meeting confirmation."""
    for item in user_timing_list:
        date = item['slot'].strftime('%a, %d %b %Y')
        time = item['slot'].strftime('%I:%M %p')
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=item['user'],
            template_name=constants.MEETING_CONFIRMATION_FRESHCHAT_TEMPLATE,
            template_data=[
                {"data": item['user'].name.title()},
                {"data": time},
                {"data": date},
            ]
        )
