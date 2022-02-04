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
        creator_number = row.get("Creator").strip()
        poc_email = row.get("POC Email").strip()

        if not creator_number and poc_email:
            print("Data not present", creator_number, poc_email)
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
            )
        except get_user_model().DoesNotExist:
            print("POC doesn't not exist: {}".format(poc_email))
            continue

        print("Creator: ", creator.__str__())
        print("POC: ", poc.__str__())

        if not dry_run:
            creator.point_of_contact = poc
            creator.save()
            print("Updated POC for Creator: {}".format(creator.id))

        print("-----")
