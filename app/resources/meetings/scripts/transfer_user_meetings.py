import csv
import datetime
from urllib import request as urllib_request

from resources.meetings import models as meeting_models
from users import models as user_models


FIELDS = [
    "Email A",
    "Email B",
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/merge_meeting_data.csv",
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print("Start", "-" * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email_a = row.get("Email A").strip()
        email_b = row.get("Email B").strip()
        # Getting the users if present.
        user_a, user_b = None, None

        try:
            user_a = user_models.User.objects.get(email=email_a)
            print("User {}".format(email_a))
        except user_models.User.DoesNotExist:
            print("*" * 5, "User Does Not Exist - {}".format(email_a))

        try:
            user_b = user_models.User.objects.get(email=email_b)
            print("User {}".format(email_b))
        except user_models.User.DoesNotExist:
            print("*" * 5, "User Does Not Exist - {}".format(email_b))

        if not (user_a and user_b):
            continue

        if user_a == user_b:
            print("Same user present twice {}".format(email_a))
            continue

        if not user_a.phone_number:
            print("User A has no phone {}".format(email_a))
        
        if user_b.phone_number:
            print("User B has phone number {}".format(email_b))


        if not dry_run:
            if not (user_a and user_b):
                print("*" * 5, "User's are not present")
                continue

            meetings_b = meeting_models.Meeting.objects.filter(participants=user_b)
            if len(meetings_b) == 0:
                print("User B has no meetings {}".format(email_b))
                continue

            for meeting in meetings_b:
                meeting.participants.add(user_a)
                meeting.participants.remove(user_b)
            

            print("Updated Meeting for users {} & {}".format(email_a, email_b))

        print("End", "-" * 80)
