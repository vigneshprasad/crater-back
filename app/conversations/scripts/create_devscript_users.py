import csv
from urllib import request as urllib_request

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from conversations import constants
from conversations import models
from conversations import serializers
from conversations import services
from users import constants as user_constants
from users import public as users_public
from wn_analytics import models as analytics_models


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/devscript_users.csv",
        dry_run=True
):

    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)
    total_users = 0
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
            username_match = get_user_model().objects.filter(username=phone_number)
            email_match = get_user_model().objects.filter(email=email)
            if username_match:
                print("Username exists")
                continue
            if email_match:
                print("Email exists")
                continue
            user, created = users_public.get_or_create_user(phone_number)
            create_or_update_str = "Created" if created else "Updated"
            print("{} for phone number: {}".format(create_or_update_str, phone_number))
            user.email = email
            user.name = name
            # Add first name and last name.
            try:
                name_list = name.split()
                user.first_name = name_list[0]
                user.last_name = " ".join(name_list[1:])
            except KeyError:
                pass

            user.save()

            # Adding user to crater group.
            crater_club_group, _ = Group.objects.get_or_create(
                name=user_constants.CRATER_CLUB_GROUP
            )

            if crater_club_group not in user.groups.all():
                user.groups.add(crater_club_group)

            profile = user.profile
            profile.opted_in_for_whatsapp = False
            print("Removed from whatsapp list")
            profile.save()

            if created:
                analytics_models.UserSource.objects.create(
                    user=user,
                    utm_source="Dev Script"
                )

            devscript_series = models.Series.objects.get(id=5)
            if devscript_series.host.pk == user.pk:
                continue

            groups_to_rsvp = services.get_series_groups_not_rsvped_by_user(
                series=devscript_series,
                user=user
            )
            print("Group to RSVP:", groups_to_rsvp)
            if not groups_to_rsvp:
                continue

            data = [
                {
                    "requester": user.pk,
                    "group": group.pk,
                    "participant_type": constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
                }
                for group in groups_to_rsvp
            ]

            serializer = serializers.RequestSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            series_requests = serializer.save()
            print("Request for groups created: ", series_requests)

            services.add_attendee_to_series(
                attendee=user, series=devscript_series, series_requests=series_requests
            )
            print("Added user as attendees")

        total_users += 1

    return total_users
