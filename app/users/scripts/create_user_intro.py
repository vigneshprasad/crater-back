from users import models
from resources.meetings import services as meeting_services


def run(emails, dry_run=True):
    """Create new intros based on the input fields for users."""

    for email in emails:

        print("Start", "*" * 30)
        print("Email: {}".format(email))

        try:
            user = models.User.objects.get(email=email)
        except models.User.DoesNotExist:
            print("User does not exist")
            continue

        if not user.has_profile:
            print("User does not have profile")
            print("End", "*" * 30)
            continue

        profile = user.profile
        first_name = user.get_display_first_name()

        user_tag = profile.new_tag.first()
        user_tag_name = user_tag.name if user_tag else None

        user_experience = profile.years_of_experience
        user_experience_str = dict(models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[profile.years_of_experience] if user_experience else None

        user_company_type = profile.company_type
        user_company_type_str = dict(models.Profile.COMPANY_TYPE_CHOICES)[profile.company_type] if user_company_type else None

        user_sector = profile.sector
        user_sector_str = dict(models.Profile.SECTOR_CHOICES)[profile.sector] if user_sector else None

        user_education = profile.education_level
        user_education_str = dict(models.Profile.EDUCATION_LEVEL_CHOICES)[profile.education_level] if user_education else None

        user_meeting_preference = meeting_services.get_latest_preference_for_user(user)
        user_meeting_preference_id = user_meeting_preference.id if user_meeting_preference else None

        user_meeting_objective = None
        user_meeting_interest = None
        user_meeting_topic = None

        if user_meeting_preference:
            user_meeting_objective = user_meeting_preference.objectives.first()
            user_meeting_interest = user_meeting_preference.interests.first()
            user_meeting_topic = user_meeting_preference.topic

        user_meeting_objective_name = user_meeting_objective.name if user_meeting_objective else None
        user_meeting_interest_name = user_meeting_interest.name if user_meeting_interest else None
        user_meeting_topic_name = user_meeting_topic.name if user_meeting_topic else None
        user_meeting_objective_or_topic_name = user_meeting_objective_name if user_meeting_objective_name else user_meeting_topic_name

        print("User Tag: {}".format(user_tag_name))
        print("User Experience: {}".format(user_experience_str))
        print("User Company Type: {}".format(user_company_type_str))
        print("User Sector: {}".format(user_sector_str))
        print("User Education: {}".format(user_education_str))
        print("User Meeting Preference: {}".format(user_meeting_preference_id))
        print("User Meeting Interest: {}".format(user_meeting_interest_name))
        print("User Meeting Objective/Topic: {}".format(user_meeting_objective_or_topic_name))

        if not user_tag_name or user_tag_name != "Student/Intern":
            introduction_string = "{} is a {} with {} of work experience. {} is currently working with a {}, in the {} sector. {} has completed a {} degree and is keen to converse about {} with {}." \
                .format(first_name, user_tag_name, user_experience_str, first_name, user_company_type_str, user_sector_str, first_name, user_education_str, user_meeting_objective_or_topic_name, user_meeting_interest_name)
        else:
            introduction_string = "{} is a {}. {} is interested in the {} sector and is pursuing a {} degree. {} is keen to converse about {}, with {}." \
                .format(first_name, user_tag_name, first_name, user_sector_str, user_education_str, first_name, user_meeting_objective_or_topic_name, user_meeting_interest_name)

        print(introduction_string)

        if not dry_run:
            if profile.introduction:
                print("User has existing introduction: {}".format(profile.introduction))

            profile.introduction = introduction_string
            profile.save()
            print("Added new introduction: {}".format(introduction_string))

        print("End", "*" * 30)
