import csv

from matching.engines import scoring_constants


def run(dry_run):
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/interest_objectives_tag_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    final_dictionary = {}

    for row in csv_reader:

        interest_objective = row["Interest-Objective"]
        all_tags = list(row.keys())
        # Removing the interest objective key from the row.
        all_tags.pop(0)

        tag_score_dict = {}
        for tag in all_tags:
            tag_score_dict[tag] = float(row.get(tag)) or 0.1

        final_dictionary[interest_objective] = tag_score_dict

    if not dry_run:
        # Update the interest objective tag score map.
        scoring_constants.INTEREST_OBJECTIVE_TAG_SCORE = final_dictionary

    return final_dictionary
