import csv

from matching import constants
from resources.meetings import choices as meeting_choices
from resources.meetings import models as meeting_models


def create_interest_objective_tag_mapping():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""
    csv_file = open('/app/matching/data/interest_objectives_tag_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    final_dictionary = {}

    for row in csv_reader:
        interest_objective = row["Interest-Objective"]
        all_tags = list(row.keys())
        all_tags.pop(0)
        tag_score_dict = {}
        for tag in all_tags:
            tag_score_dict[tag] = float(row.get(tag)) or 0.1

        final_dictionary[interest_objective] = tag_score_dict

    return final_dictionary


def create_objective_map_scores():
    """Curates a dictionary of dictionaries from Objective to objective engine CSV."""
    csv_file = open('/app/matching/data/objective_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    objective_score_map = {}

    for row in csv_reader:
        objectives = row["Objectives"]
        all_objectives = list(row.keys())
        all_objectives.pop(0)
        objective_score_dict = {}
        for objective in all_objectives:
            objective_score_dict[objective] = float(row.get(objective)) or 0.1

        objective_score_map[objectives] = objective_score_dict

    return objective_score_map


def create_tag_map_scores():
    csv_file = open('/app/matching/data/tags_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tags_score_map = {}

    for row in csv_reader:
        tags = row["Tags"]
        all_tags = list(row.keys())
        all_tags.pop(0)
        tags_score_dict = {}
        for tag in all_tags:
            tags_score_dict[tag] = row.get(tag) or 0.1
            tags_score_dict[tag] = float(tags_score_dict[tag])

        tags_score_map[tags] = tags_score_dict

    return tags_score_map


def map_objectives_to_new_model_field(dry_run=True):

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
        new_objective = constants.OLD_OBJECTIVES_TO_NEW_OBJECTIVES_MAP.get(objective_value)
        print("New Objective Value: {}".format(new_objective))

        if not dry_run:
            new_objective_obj, _ = meeting_models.Objective.objects.get_or_create(
                name=new_objective
            )
            preference.objectives.add(new_objective_obj)

        print("End", "-" * 80)
