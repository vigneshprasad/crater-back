from users import models
from resources.meetings import models as meeting_models
from users import choices

def run(emails, dry_run=True):
    """Create new intros based on the input fields for users."""

    for email in emails:
        user = models.User.objects.get(email=email)
        print("Start", "*"*30)
        print("Email: ", email)
        if not user.has_profile:
            print("User does not have profile")
            print("End", "*" * 30)
            continue
        
        profile = user.profile
        first_name = user.get_display_first_name()

        if len(user.profile.new_tag.all()) == 0:
            print("User does not have a tag")
            print("End", "*" * 30)
            continue
        tag = profile.new_tag.all().first().name

        if not user.profile.years_of_experience:
            print("User does not have years of experience")
            print("End", "*" * 30)
            continue
        years_of_experience = dict(models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[profile.years_of_experience]
        
        if not user.profile.company_type:
            print("User does not have company type")
            print("End", "*" * 30)
            continue
        company_type = dict(models.Profile.COMPANY_TYPE_CHOICES)[profile.company_type]

        if not user.profile.sector:
            print("User does not have sector")
            print("End", "*" * 30)
            continue
        sector = dict(models.Profile.SECTOR_CHOICES)[profile.sector]

        if not user.profile.education_level:
            print("User does not have education level")
            print("End", "*" * 30)
            continue
        education_level = dict(models.Profile.EDUCATION_LEVEL_CHOICES)[profile.education_level]
        
        meeting_preference = meeting_models.MeetingPreference.objects.filter(user=user).last()
        if not meeting_preference:
            print("User does not have a meeting preference")
            print("End", "*" * 30)
            continue
        
        if not meeting_preference.objectives.first():
            print("User does not have an objective")
            print("End", "*" * 30)
            continue
        meeting_objective = meeting_preference.objectives.first().name

        if not meeting_preference.interests.first():
            print("User does not have an interest")
            print("End", "*" * 30)
            continue
        meeting_interest = meeting_preference.interests.first().name


        if (tag == 'Student/Intern'):
            introduction_string = "{} is a {}. {} is interested in the {} sector and is pursuing a {} degree. {} is keen to converse about {}, with {}." \
                .format(first_name, tag, first_name, sector, education_level, first_name, meeting_objective, meeting_interest)
        else :
            introduction_string = "{} is a {} with {} of work experience. {} is currently working with a {}, in {} sector. {} has completed a {} degree and is keen to converse about {} with {}." \
                .format(first_name, tag, years_of_experience, first_name, company_type, sector, first_name, education_level, meeting_objective, meeting_interest)    
        
        if dry_run:
            print(introduction_string)

        if not dry_run:
            if(profile.introduction):
                print("User has existing intro: {}".format(profile.introduction))
            profile.introduction = introduction_string
            profile.save()
            print("Added new introduction: {}".format(introduction_string))

        print("End", "*" * 30)
