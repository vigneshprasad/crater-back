import csv
import ast
import datetime
from urllib import request as urllib_request

from integrations.freshchat import public as freshchat_public
from integrations.google import public as google_public
from conversations import models
from conversations import services
from conversations import tasks
from resources.meetings import models as meeting_models
from users import models as user_models


# TODO(Nishant): Create tag to interest mapping and use that to populate interests in the group.
FIELDS = [
    "Users",
    "Topic",
    "Meeting Time (%d/%m%/%y %H:%M)",
    "Interests"
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/conversations_data.csv",
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print("Start", "-" * 80)
        # Getting all the fields in the right format.
        emails_score_str = row.get("Users").strip()
        topic = row.get("Topic").strip()
        meeting_time = row.get("Meeting Time").strip()
        interests_str = row.get("Interests").strip()

        emails_score_list = ast.literal_eval(emails_score_str)
        emails_list = [email_score[0] for email_score in list(emails_score_list)]

        interests_list = interests_str.split(",")

        users_list = []
        for email in emails_list:
            try:
                user = user_models.User.objects.get(email=email)
            except user_models.User.DoesNotExist:
                print("Email Does Not Exist: ", email)
                continue
            users_list.append(user)

        topic_obj = None
        try:
            topic_obj = models.Topic.objects.get(name=topic)
        except models.Topic.DoesNotExist:
            print("Topic Does Not Exist: ", topic)

        start = datetime.datetime.strptime(meeting_time, "%d/%m/%y %H:%M")
        end = start + datetime.timedelta(hours=1)

        print("Start: {}".format(start))
        print("End: {}".format(end))

        interests_objs = []
        for interest in interests_list:
            try:
                interest_obj = meeting_models.Interest.objects.get(name=interest)
            except meeting_models.Interest.DoesNotExist:
                print("Interest Does Not Exist: ", interest)
                continue
            interests_objs.append(interest_obj)

        if not dry_run:

            print("Creating Group")
            group = services.create_group_conversation(users_list, interests_objs, topic_obj, start, end)
            print("Group Created: {}".format(group.id))

            print("Creating Calendar event for group")
            event_id = google_public.create_calendar_event_for_conversations(group)
            print("Created Calendar event for group: {}".format(event_id))

            print("Sending Confirmation Email")
            tasks.send_conversation_confirmation_email_for_group(group)
            print("Sent Confirmation Email")

            print("Sending Confirmation WhatsApp")
            freshchat_public.send_conversation_confirmation_rsvp_for_group(group)
            print("Sent Confirmation WhatsApp")

        print("End", "-" * 80)
