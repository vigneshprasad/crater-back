import csv

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from django.contrib.auth.models import Group

from users import models
from tags import models as tags_models


def run(
        file_name='/app/users/data/users_data.csv',
        dry_run=True
):

    reader = csv.DictReader(open(file_name))
    for row in reader:
        full_name = row.get('Full Name', '').strip()
        linkedin_url = _validate_url_and_return(row.get('Linkedin'))
        email = row.get('Email ID').strip()
        phone_number = row.get('Phone Number') or None

        raw_interests = row.get('Interests', '').split(',')
        interests = [interest.strip() for interest in raw_interests]
        raw_objectives = row.get('Objectives', '').split(',')
        objectives = [objective.strip() for objective in raw_objectives]

        username = full_name.split()[0]

        print("Start", "*"*80)

        print("Creating user for email: {}".format(email))
        print("Username: {}".format(username))
        print("Name: {}".format(full_name))
        print("Phone Number: {}".format(phone_number))
        print("Objectives: {}".format(objectives))
        print("Interests: {}".format(interests))
        print("Linkedin Url: {}".format(linkedin_url))

        if not dry_run:
            user, profile = create_user_and_profile(
                username=username,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                objectives=objectives,
                interests=interests,
                linkedin_url=linkedin_url
            )

        print("End", "-"*80)


def create_user_and_profile(
        full_name,
        email,
        phone_number,
        linkedin_url,
        username=None,
        interests=None,
        objectives=None,
        source=None,
):
    user_created = False

    if not username:
        username = full_name.split()[0]
    if not phone_number:
        phone_number = None

    # Creating User.
    try:
        user = models.User.objects.get(email=email)
    except models.User.DoesNotExist:
        user = models.User.objects.create(
            email=email,
            username=username,
            phone_number=phone_number,
            new_phone_number=phone_number,
            name=full_name,
            source=source
        )
        
        user.set_unusable_password()
        user.save()
        user_created = True
    
    group = Group.objects.get(name="User")
    user.groups.add(group)

    # Adding Objectives to User.
    if objectives:
        objectives = tags_models.Objective.objects.filter(
            name__in=objectives
        )

    objectives = tags_models.Objective.objects.filter(
        name='Meet Professionals & Founders'
    ) if not objectives else objectives

    for objective in objectives:
        user.objectives.add(objective)

    # Creating Profile
    profile, created = models.Profile.objects.get_or_create(
        user=user
    )
    profile_created = created
    profile.linkedin_url = linkedin_url
    profile.save()

    # Adding Interests to Profile.
    if interests:
        interests = tags_models.Interests.objects.filter(
            name__in=interests
        )
        for interest in interests:
            profile.interests.add(interest)

    created_or_updated_user = 'Created' if user_created else 'Updated'
    print("{} user: {}".format(created_or_updated_user, user.pk))
    created_or_updated_profile = 'Created' if profile_created else 'Updated'
    print("{} profile: {}".format(created_or_updated_profile, profile.pk))

    return user, profile


def _validate_url_and_return(url):
    if not url:
        return None

    url = url.strip()
    try:
        validator = URLValidator()
        validator(url)
    except ValidationError:
        return None

    return url
