import csv
from urllib import request as urllib_request

from conversations import constants
from conversations import models
from conversations import serializers
from conversations import services
from users import public as users_public


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/devscript_users.csv",
        dry_run=True
):

    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:

        print("-----")
        email = row.get("Email", "").strip()
        name = row.get("Name", "").strip()
        phone_number = row.get("Username", "").strip()

        if not (email and name and phone_number):
            print("Details not present.")

        print("Username: ", phone_number)
        print("Email: ", email)
        print("Name: ", name)

        if not dry_run:
            user, created = users_public.get_or_create_user(phone_number)
            create_or_update_str = "Created" if created else "Updated"
            print("{} for phone number: {}".format(create_or_update_str, phone_number))
            user.email = email
            user.name = name
            user.save()

            profile = user.profile
            profile.opted_in_for_whatsapp = False
            print("Removed from whatsapp list")
            profile.save()

            devscript_series = models.Series.objects.get(id=5)
            if devscript_series.host.pk == user.pk:
                continue

            groups_to_rsvp = services.get_series_groups_not_rsvped_by_user(
                series=devscript_series,
                user=user
            )

            if not groups_to_rsvp:
                continue

            data = [
                {
                    "requester": user,
                    "group": group.pk,
                    "participant_type": constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
                }
                for group in groups_to_rsvp
            ]

            serializer = serializers.RequestSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            series_requests = serializer.save()

            services.add_attendee_to_series(
                attendee=user, series=devscript_series, series_requests=series_requests
            )
