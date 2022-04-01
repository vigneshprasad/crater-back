import csv
from urllib import request as urllib_request

from django.contrib.auth import get_user_model

from crater.creator import models


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/creator_poc.csv",
        dry_run=True
):

    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:

        print("-----")
        creator_number = row.get("Creator Phone Number").strip()
        poc_email = row.get("POC Email").strip()
        prospector_email = row.get("Prospector Email").strip()

        if not creator_number:
            print("Data not present: ", creator_number)
            continue

        try:
            creator = models.Creator.objects.get(
                user__username=creator_number
            )
        except models.Creator.DoesNotExist:
            print("Creator doesn't not exist: {}".format(creator_number))
            continue

        try:
            poc = get_user_model().objects.get(
                email=poc_email
            ) if poc_email else None
        except get_user_model().DoesNotExist:
            print("POC doesn't not exist: {}".format(poc_email))
            continue

        try:
            prospector = get_user_model().objects.get(
                email=prospector_email
            ) if prospector_email else None
        except get_user_model().DoesNotExist:
            print("Prospector doesn't not exist: {}".format(poc_email))
            continue

        print("Creator: ", creator.__str__())
        print("POC: ", poc.__str__())
        print("Prospector: ", prospector.__str__())

        if not dry_run:
            if poc:
                creator.point_of_contact = poc
            if prospector:
                creator.prospector = prospector
            creator.save()
            print("Updated POC and prospector for Creator: {}".format(creator.id))

        print("-----")
