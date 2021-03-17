import csv
from urllib import request as urllib_request

from users import models
from resources.meetings import models as meeting_models
from resources.meetings import services as meeting_services

FIELDS = [
    "Email ID",
    "Objectives",
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/user_objectives.csv",
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:

        print("Start", "-" * 80)
        email = row["Email ID"].strip()
        raw_objectives = row.get("Objectives", "").split(",")
        objectives = [objective.strip() for objective in raw_objectives]

        user = models.User.objects.filter(email=email).first()
        if not user:
            print("User does not exist")
            print("End", "*" * 30)
            continue

        meeting_preference = meeting_services.get_latest_meeting_preference(user)
        if not meeting_preference:
            print("User does not have a meeting preference")
            print("End", "*" * 30)
            continue

        if meeting_preference.objectives.first():
            print("User already has objective")
            print("End", "*" * 30)
            continue

        print("Objectives: {}".format(objectives))

        if not dry_run:
            objective_objects = meeting_models.Objective.objects.filter(name__in=objectives)
            for objective_object in objective_objects:
                meeting_preference.objectives.add(objective_object)
            print("Added new objective: {}".format(objective_objects))

        print("End", "-" * 80)
