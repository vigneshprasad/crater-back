import csv

from django.contrib.auth import get_user_model

from devices import private


def run(dry_run=True):
    """Creates devices from CSV."""
    csv_file = open("/app/devices/data/user_device_details.csv", mode="r")
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        print("*"*30)
        email = row.get("Email").lower()
        device_name = row.get("Device Name").lower()
        device_model = row.get("Device Model").lower()
        device_price = int(row.get("Price"))

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            print("No User for email: {}".format(email))
            continue

        print("User: {}".format(user.email))
        print("Name: {}".format(device_name))
        print("Model: {}".format(device_model))
        print("Price: {}".format(device_price))

        if not dry_run:
            print("Creating user device")
            user_device = private.create_or_update_user_device(user, device_name, device_model, device_price)
            print("User Device created: {}".format(user_device.id))

        print("*"*30)
