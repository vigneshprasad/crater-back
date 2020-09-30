from resources.meetings import choices
from resources.meetings import models
from users import models as user_models

DEFAULT_OBJECTIVE_NAME = "Meet Interesting People"


def run(dry_run=True):
    print("Starting population of interests")
    for user in user_models.User.objects.all():

        latest_meeting_preference = user.meeting_preferences.last()
        if not latest_meeting_preference:
            print("No meeting preference")
            continue

        print("-" * 80)
        print(user.email)

        profile_interests = list(user.profile.interests.all().values_list('name', flat=True))
        preference_interests = list(latest_meeting_preference.interests.all().values_list('name', flat=True))

        all_objectives = latest_meeting_preference.objective
        all_interests = profile_interests + preference_interests

        print("All selected interest for user: {}".format(all_interests))
        print("All selected objective for user: {}".format(all_objectives))

        if not dry_run:

            print("Adding interests for user.")
            interests = models.Interest.objects.filter(name__in=all_interests)
            for interest in interests:
                latest_meeting_preference.interests.add(interest)

            print("Adding interest for user.")
            # Get the objective name from the old objective field.
            old_objective = latest_meeting_preference.objective
            old_objective_name = None
            for key, name in choices.OBJECTIVE_CHOICES:
                if key == old_objective:
                    old_objective_name = name

            objective_name = old_objective_name if old_objective_name else DEFAULT_OBJECTIVE_NAME
            new_objective = models.Objective.objects.filter(
                name=objective_name
            ).last()

            if not new_objective:
                print("No objective for with the given name: {}".format(objective_name))
                continue

            latest_meeting_preference.objectives = new_objective
            latest_meeting_preference.save()

        print("-" * 80)
