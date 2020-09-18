import csv
import datetime
from urllib import request as urllib_request

from users import models as user_models
from integrations.freshchat import constants
from integrations.freshchat import freshchat_service


FIELDS = [
    "Email",
    "Meeting Time (%m/%d%/%Y %H:%M)"
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_confirmation_whatsapp.csv",
        dry_run=True
):
    meeting_confirmation_data = []

    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print('Start', '-' * 80)

        email = row["Email"].strip()
        meeting_time = row["Meeting Time"]
        meeting_datetime = datetime.datetime.strptime(meeting_time, '%m/%d/%Y %H:%M')

        try:
            user = user_models.User.objects.get(email=email)
            print('User {}'.format(user.email))
            print('Slot {}'.format(meeting_datetime))
            meeting_confirmation = {
                'user': user,
                'slot': meeting_datetime
            }
            meeting_confirmation_data.append(meeting_confirmation)
        except user_models.User.DoesNotExist:
            print('User not available for {}'.format(email))
            continue

        print('End', '-' * 80)

    print('*'*80)
    print('Total Users: {}'.format(len(meeting_confirmation_data)))
    print('*' * 80)

    if not len(meeting_confirmation_data):
        print("No Meeting Data Found.")

    if not dry_run:
        _send_meeting_confirmation_messages(meeting_confirmation_data)


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
