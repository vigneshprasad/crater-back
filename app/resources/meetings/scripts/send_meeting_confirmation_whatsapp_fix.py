import csv
import datetime
from urllib import request as urllib_request

from users import models as user_models
from integrations.freshchat import constants
from integrations.freshchat import freshchat_service


FIELDS = [
    "Email",
    "Meeting Start Time (%d/%m%/%y %H:%M)",
    "Meeting End Time (%d/%m%/%y %H:%M)",
    "Message"
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_confirmation_whatsapp_fix.csv",
        dry_run=True
):
    meeting_confirmation_data = []

    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print('Start', '-' * 80)

        email = row["Email"].strip()
        meeting_start_time = row["Meeting Start Time"]
        meeting_end_time = row["Meeting End Time"]
        message = row.get("Message").strip()
        meeting_start_datetime = datetime.datetime.strptime(meeting_start_time, '%d/%m/%y %H:%M')
        meeting_end_datetime = datetime.datetime.strptime(meeting_end_time, '%d/%m/%y %H:%M')

        try:
            user = user_models.User.objects.get(email=email)
            print('User {}'.format(user.email))
            print('Start Slot {}'.format(meeting_start_datetime))
            print('End Slot {}'.format(meeting_end_datetime))
            print('Message: {}'.format(message))
            meeting_confirmation = {
                'user': user,
                'start_slot': meeting_start_datetime,
                'end_slot': meeting_end_datetime,
                'message': message
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
        date = item['start_slot'].strftime('%a, %d %b %Y')
        final_date = "{} ({})".format(date, item["message"])
        start_time = item['start_slot'].strftime('%I:%M %p')
        end_time = item['end_slot'].strftime('%I:%M %p')
        time = "{} - {}".format(start_time, end_time)
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=item['user'],
            template_name=constants.MEETING_CONFIRMATION_FRESHCHAT_TEMPLATE,
            template_data=[
                {"data": item['user'].name.title()},
                {"data": time},
                {"data": final_date},
            ]
        )
