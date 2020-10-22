import csv

from matching.engines import scoring_constants


def run(dry_run=True):
    """Curates a dictionary of dictionaries from Objective to objective engine CSV."""

    csv_file = open('/app/matching/data/objective_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    objective_score_map = {}

    for row in csv_reader:

        objectives = row["Objectives"]
        all_objectives = list(row.keys())
        # Removing the objective key from row.
        all_objectives.pop(0)

        objective_score_dict = {}
        for objective in all_objectives:
            objective_score_dict[objective] = float(row.get(objective)) or 0.1

        objective_score_map[objectives] = objective_score_dict

    if not dry_run:
        # Update the objective to objective map in the constants file.
        scoring_constants.OBJECTIVE_TO_OBJECTIVE_SCORES = objective_score_map

    return objective_score_map
