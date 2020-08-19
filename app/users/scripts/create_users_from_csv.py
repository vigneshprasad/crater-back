import csv
from django.contrib.auth.models import UserManager
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from resources.meetings import models
from tags import models as tags_models
from users import models


def run(
        file_name='/app/users/data/users_data.csv',
        dry_run=True
):

    reader = csv.DictReader(open(file_name))

    for row in reader:
        full_name = row.get('Full Name', ',').strip()
        raw_interests = row.get('Interests', '').split(',')
        interests = [interest.strip() for interest in raw_interests]
        raw_objectives = row.get('Objectives', '').split(',')
        objectives = [objective.strip() for objective in raw_objectives]
        linkedin_url = _validate_url_and_return(row.get('Linkedin', ''))
        email = row.get('Email ID').strip()
        phone_number = row.get('Phone Number', '').strip()

        username = full_name.split()[0]
        print("Start", "*"*80)
        print("Creating user for email: {}".format(email))

        print("Username: {}".format(username))
        print("Phone Number: {}".format(phone_number))

        user_created = False
        profile_created = False

        if not dry_run:
            try:
                user = models.User.objects.get(email=email)
            except models.User.DoesNotExist:
                user_manager = UserManager()
                user = user_manager.create_user(
                    username=username,
                    email=email,
                    new_phone_number=phone_number,
                    phone_number=phone_number
                )
                user_created = True

        objectives = tags_models.Objective.objects.filter(
            name__in=objectives
        )
        print("Objectives: {}".format(','.join([objective.name for objective in objectives])))

        if not objectives:
            objectives = tags_models.Objective.objects.get(
                name='Meet Professionals & Founders'
            )

        if not dry_run:
            user.objectives.add(objectives)

        print("Profile creation starting......")
        print("Linkedin Url: {}".format(linkedin_url))
        interests = tags_models.Interests.objects.filter(
            name__in=interests
        )
        print("Interests: {}".format(','.join([interest.name for interest in interests])))

        if not dry_run and interests:
            profile, created = models.Profile.objects.get_or_create(
                user=user
            )
            profile_created = created
            profile.linkedin_url = linkedin_url
            profile.save()
            profile.interests.add(interests)

        if not dry_run:
            created_or_updated_user = 'Created' if user_created else 'Updated'
            print("{} user: {}".format(created_or_updated_user, user.pk))
            created_or_updated_profile = 'Created' if profile_created else 'Updated'
            print("{} profile: {}".format(created_or_updated_profile, profile.pk))

        print("End", "-"*80)


def _validate_url_and_return(url):
    url = url.strip()
    try:
        validator = URLValidator()
        validator(url)
    except ValidationError:
        return None
    return url
