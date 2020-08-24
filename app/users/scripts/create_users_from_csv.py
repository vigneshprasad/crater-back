import csv

from allauth.account.models import EmailAddress
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from django.contrib.auth.models import Group

from users import models
from tags import models as tags_models


user_source = 'https://worknetwork.typeform.com/to/MNbvcw7y'


def run(
        file_name='/app/users/data/users_data.csv',
        dry_run=True
):

    reader = csv.DictReader(open(file_name))
    for row in reader:
        print("Start", "*" * 80)

        full_name = row.get('Full Name', '').strip()
        linkedin_url = _validate_url_and_return(row.get('Linkedin'))
        email = row.get('Email ID').strip()
        phone_number = row.get('Phone Number') or None

        raw_interests = row.get('Interests', '').split(',')
        interests = [interest.strip() for interest in raw_interests]
        raw_objectives = row.get('Objectives', '').split(',')
        objectives = [objective.strip() for objective in raw_objectives]
        raw_tags = row.get('Objectives', '').split(',')
        tags = [tag.strip() for tag in raw_tags]
        public_introduction = row.get('Introduction')

        if not full_name:
            print("Name not provided for the user: {}".format(email))
            print("End", "-" * 80)
            continue

        if not email:
            print("Email is not provided for the user: {}".format(full_name))
            print("End", "-" * 80)
            continue

        username = full_name.split()[0]

        print("Creating user for email: {}".format(email))
        print("Username: {}".format(username))
        print("Name: {}".format(full_name))
        print("Phone Number: {}".format(phone_number))
        print("Source: {}".format(user_source))
        print("Objectives: {}".format(objectives))
        print("Interests: {}".format(interests))
        print("Tags: {}".format(tags))
        print("Linkedin Url: {}".format(linkedin_url))
        print("Introduction: {}".format(public_introduction))

        if not dry_run:
            user, profile = create_user_and_profile(
                username=username,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                objectives=objectives,
                interests=interests,
                linkedin_url=linkedin_url,
                source=user_source,
                tags=tags,
                introduction=public_introduction
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
        tags=None,
        introduction=None
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

        # Create Email address object for user.
        email_address = EmailAddress.objects.create(
            primary=True,
            user=user,
            email=email
        )
        print("Email Address Object: {}".format(email_address.pk))

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
    profile.name = full_name
    profile.linkedin_url = linkedin_url
    profile.public_introduction = introduction
    profile.save()

    # Adding Interests to Profile.
    if interests:
        interests = tags_models.Interests.objects.filter(
            name__in=interests
        )
        for interest in interests:
            profile.interests.add(interest)

    if tags:
        tags = tags_models.Tag.objects.filter(
            name__in=tags
        )
        for tag in tags:
            profile.tags.add(tag)

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
