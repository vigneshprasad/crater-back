from matching import constants
from resources.meetings import choices as meeting_choices
from resources.meetings import models as meeting_models


def run(dry_run=True):

    for preference in meeting_models.MeetingPreference.objects.all():

        print("Start", "-"*80)
        print("Email: {}".format(preference.user.email))
        if preference.objectives.all():
            continue

        objective_key = preference.objective
        print("Old Objective Key: {}".format(objective_key))
        if not objective_key:
            continue

        objective_choice_dict = dict(meeting_choices.OBJECTIVE_CHOICES)
        objective_value = objective_choice_dict.get(objective_key)
        print("Actual Objective Value: {}".format(objective_value))
        new_objective = constants.OLD_OBJECTIVES_TO_NEW_OBJECTIVES_MAP.get(objective_value) or objective_value
        print("New Objective Value: {}".format(new_objective))

        if not dry_run:
            new_objective_obj, _ = meeting_models.Objective.objects.get_or_create(
                name=new_objective
            )
            preference.objectives.add(new_objective_obj)

        print("End", "-" * 80)
