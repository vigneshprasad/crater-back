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


def rsvp_pixed_users(dry_run=True):

    sources = analytics_models.UserSource.objects.filter(utm_source="Picxele")
    group = models.Group.objects.get(id=1133)
    print(group)

    for source in sources:
        print("------")
        user = source.user
        print(source.user)
        request = models.Request.objects.filter(
            requester=user,
            group=group,
            participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
        )
        if request:
            print("Already RSVPed")
            continue

        if not dry_run:
            data = {
                "requester": user.pk,
                "group": group.pk,
                "participant_type": constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
            }

            serializer = serializers.RequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            request = serializer.save()
            print("Request for group created: ", request)
            services.add_attendee_to_group_for_request(user, request)

        print("------")


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/add_users.csv",
        dry_run=True
):

    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)
    total_users = 0
    group = models.Group.objects.get(id=1209)
    print(group)

    for row in reader:

        print("-----")
        email = row.get("Email", "").strip()
        first_name = row.get("First name", "").strip()
        last_name = row.get("Last name", "").strip()
        phone_number = row.get("Phone ", "").strip()

        name = first_name + " " + last_name

        if not (email and name and phone_number):
            # If not username, email and name.
            print("Details not present.")
            print("Username: ", phone_number)
            print("Email: ", email)
            print("Name: ", name)
            continue

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
            user.first_name = first_name
            user.last_name = last_name
            user.name = name

            # Add first name and last name.
            # try:
            #     name_list = name.split()
            #     user.first_name = name_list[0]
            #     user.last_name = " ".join(name_list[1:])
            # except KeyError:
            #     pass

            user.save()

            # Adding user to crater group.
            crater_club_group, _ = Group.objects.get_or_create(
                name=user_constants.CRATER_CLUB_GROUP
            )

            if crater_club_group not in user.groups.all():
                user.groups.add(crater_club_group)

            profile = user.profile

            if created:
                analytics_models.UserSource.objects.create(
                    user=user,
                    utm_source="Anand K Rathi"
                )

            data = {
                "requester": user.pk,
                "group": group.pk,
                "participant_type": constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
            }
            serializer = serializers.RequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            request = serializer.save()
            print("Request for groups created: ", request)

            services.add_attendee_to_group_for_request(
                user,
                request
            )
            print("Added user as attendee")

        total_users += 1

    return total_users
