import urllib
import csv

from django.contrib.auth import get_user_model
from crater.creator import models as crater_models

FIELDS = [
    "Email",
    "Subscriber Count",
    "Order",
    "Certified",
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/creator_data.csv",
        dry_run=True
):
    response = urllib.request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print("Start", "-" * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email = row.get("Email").strip()
        subscriber_count = row.get("Subscriber Count").strip() if row.get("Subscriber Count") else 0
        order = row.get("Order").strip() if row.get("Order") else 0
        certified = row.get("Certified").strip().capitalize()

        try:
            user = get_user_model().objects.get(email=email)
            creator = crater_models.Creator.objects.get(user=user)
        except get_user_model().DoesNotExist:
            print("User does not exist with this email: {}".format(email))
            continue
        except crater_models.Creator.DoesNotExist:
            print("Creator does not exist with this email: {}".format(email))
            continue

        print(
            "Updating creator information, {} - subscriber_count: {}, order: {}, certified: {}".format(
                email, subscriber_count, order, certified
            )
        )

        if not dry_run:
            creator.number_of_subscribers = int(subscriber_count)
            creator.order = int(order)
            creator.certified = certified
            creator.save()
