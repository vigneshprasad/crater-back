from django.contrib.auth import get_user_model
from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.creator import models as crater_models

FIELDS = [
    "Email",
    "Subscriber Count",
    "Order",
]


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/creator_data.csv",
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print("Start", "-" * 80)
        row = dict(row)
        # Getting all the fields in the right format.
        email = row.get("Email").strip()
        subscriber_count = row.get("Subscriber Count").strip()
        order = row.get("Order").strip()
        user = get_user_model.objects.get(email=email)
        creator = crater_models.Creator.objects.get(user=user)
        if not creator:
            print("Creator does not exist with this email{}".format(email))

        print("Updating creator information, {} - followers: {}, order: {}").format(email, subscriber_count, order)

        if dry_run:
            creator.subscriber_count = subscriber_count
            creator.order = order
            creator.save()
            
                    
        