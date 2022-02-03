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

        print("*"*30)
        creator_number = row.get("Creator").strip()
        poc_number = row.get("POC").strip()

        if not creator_number and poc_number:
            print("Data not present", creator_number, poc_number)
            continue

        creator = models.Creator.objects.get(
            user__username=creator_number
        )
        poc = get_user_model().objects.get(
            username=poc_number
        )
        print("Creator: ", creator.__str__())
        print("POC: ", poc.__str__())

        if not dry_run:
            creator.point_of_contact = poc
            creator.save()
            print("Updated POC for Creator: {}".format(creator.id))