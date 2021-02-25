import csv
from urllib import request as urllib_request

from allauth.account.models import EmailAddress
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from django.contrib.auth.models import Group

from users import models
from users import choices
from tags import models as tags_models

from wn_analytics import models as wn_analytics_models

FIELDS = [
    'Full Name',
    'Email ID',
    'Objectives',
    'Introduction',
    'Phone Number',
    'Linkedin Url'
]

DEFAULT_OBJECTIVE = 'Meet Professionals & Founders'

USER_SOURCE = 'https://worknetwork.typeform.com/to/MNbvcw7y'


def run(
        file_url='https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/new_users_csv.csv',
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print("Start", "-" * 80)

        full_name = row.get('Full Name', '').strip()
        linkedin_url = _validate_url_and_return(row.get('Linkedin'))
        email = row.get('Email ID').strip()
        phone_number = row.get('Phone Number') or None
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
        print("Source: {}".format(USER_SOURCE))
        print("Objectives: {}".format(objectives))
        print("Tags: {}".format(tags))
        print("Linkedin Url: {}".format(linkedin_url))
        print("Introduction: {}".format(public_introduction))

        if not dry_run:
            create_user_and_profile(
                username=username,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                objectives=objectives,
                linkedin_url=linkedin_url,
                source=USER_SOURCE,
                tags=tags,
                introduction=public_introduction
            )

        print("End", "-" * 80)


def create_user_and_profile(
        full_name,
        email,
        phone_number,
        linkedin_url,
        username=None,
        objectives=None,
        source=None,
        new_source=None,
        tags=None,
        introduction=None,
        utm_source=None,
        utm_campaign=None,
        years_of_experience=None,
        company_type=None,
        education_level=None,
        sector=None
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
            name=full_name,
            source=source
        )
        user.set_unusable_password()
        user.save()
        user_created = True

        if new_source:
            user.new_source = new_source

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

    # Creating Analytics Object
    if utm_source or utm_campaign:
        wn_analytics_models.UserSource.objects.create(
            user=user,
            utm_source=utm_source,
            utm_campaign=utm_campaign
        )

    objectives = tags_models.Objective.objects.filter(
        name=DEFAULT_OBJECTIVE
    ) if not objectives else objectives

    for objective in objectives:
        user.objectives.add(objective)

    user.save()

    # Creating Profile
    profile, created = models.Profile.objects.get_or_create(
        user=user
    )
    profile_created = created
    profile.name = full_name
    profile.linkedin_url = linkedin_url
    profile.public_introduction = introduction

    profile.years_of_experience = choices.EXPERIENCE_STR_TO_ENUM.get(years_of_experience)
    profile.company_type = choices.COMPANY_TYPE_STR_ENUM.get(company_type)
    profile.education_level = choices.EDUCATION_LEVEL_STR_TO_ENUM.get(education_level)
    profile.sector = choices.SECTOR_TYPE_STR_TO_ENUM.get(sector)

    profile.save()

    # Add tags to profile.
    if tags:
        tags = tags_models.Tag.objects.filter(
            name__in=tags,
            is_active=True
        )
        for tag in tags:
            profile.new_tag.add(tag)

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
