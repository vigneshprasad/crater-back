from resources.meetings import choices
from resources.meetings import models
from users import models as user_models
from tags import models as tags_models


def crete_meeting_interests():
    tags_interests = tags_models.Interests.objects.all()
    for i in tags_interests:
        interest = models.Interest.objects.create(
            name=i.name,
            icon=i.icon
        )
        print("Created meeting interest: {}".format(interest.name))


def create_meeting_objectives():
    for key, name in choices.OBJECTIVE_CHOICES:
        objective = models.Objective.objects.create(
            name=name
        )
        print("Created meeting objective: {}".format(objective.name))


def run(dry_run=True):

    print("Creating meeting interests and objectives.")
    crete_meeting_interests()
    create_meeting_objectives()
    print("Created")
    print("Starting population of interests")
    for user in user_models.User.objects.all():
        print("-"*80)
        print(user.email)
        profile_interests = list(user.profile.interests.all().values_list('name', flat=True))
        preference_interests = list(user.meeting_preferences.last().interests.all().values_list(
            'name',
            flat=True
        )) if user.meeting_preferences.last() else None
        all_interests = profile_interests + preference_interests
        print("All selected interest for user: ".format(all_interests))

        if not dry_run:
            print("Adding interests for user {}".format(p.user.email))
            latest_meeting_preference = user.meeting_preferences.last()
            if not latest_meeting_preference:
                print("No meeting preference")
                continue
            interests = models.Interest.objects.filter(name__in=all_interests)
            for interest in interests:
                latest_meeting_preference.interests.add(interest)

        print("-" * 80)