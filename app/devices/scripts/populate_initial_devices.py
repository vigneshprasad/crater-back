import csv

from devices import private


def run(dry_run=True):
    """Creates devices from CSV."""
    csv_file = open("/app/devices/data/device_details.csv", mode="r")
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        print("*"*30)
        device_name = row.get("Manufacturer").lower()
        device_model = row.get("Model").lower()
        device_price = int(row.get("Price"))

        print("Name: {}".format(device_name))
        print("Model: {}".format(device_model))
        print("Price: {}".format(device_price))

        if not dry_run:
            print("Creating the device")
            device = private.create_or_update_device(device_name, device_model, device_price)
            print("Device created: {}".format(device.id))

        print("*"*30)
