import csv


from users import choices
from users import models


def run(dry_run=True):
    csv_file = open('/app/users/data/new_field_data_population.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        print("Start", "*"*30)
        email = row["Email"].strip()
        experience = row["Years of experience"].strip()
        company_type = row["Company type"].strip()
        education_level = row["Education level"].strip()

        print(email)
        try:
            user = models.User.objects.get(email=email)
        except models.User.DoesNotExist:
            print("No user")
            continue

        if not user.has_profile:
            print("No profile")
            continue

        profile = user.profile
        print("Years of experience: {}".format(experience))
        print("Company type: {}".format(company_type))
        print("Education level: {}".format(education_level))

        if not dry_run:
            experience_enum = choices.EXPERIENCE_STR_TO_ENUM.get(experience)
            company_type_enum = choices.COMPANY_TYPE_STR_ENUM.get(company_type)
            education_level_enum = choices.EDUCATION_LEVEL_STR_TO_ENUM.get(education_level)

            profile.years_of_experience = experience_enum
            profile.company_type = company_type_enum
            profile.education_level = education_level_enum
            profile.save()
            print("Profile updated")
        print("End", "*"*30)
