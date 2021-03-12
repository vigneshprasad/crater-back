import csv

from matching.engines import scoring_constants


def run(dry_run=False):
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/tag_to_interest_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tag_to_interest_scores = {}

    for row in csv_reader:
        print(row)
        interest_objective = row["Tag-Interest"]
        all_tags = list(row.keys())
        # Removing the interest objective key from the row.
        all_tags.pop(0)
        tag_score_dict = {}
        for tag in all_tags:
            tag_score_dict[tag] = int(row.get(tag)) or 0

        tag_to_interest_scores[interest_objective] = tag_score_dict

    if not dry_run:
        # Update the interest objective tag score map.
        scoring_constants.INTEREST_OBJECTIVE_TAG_SCORE = tag_to_interest_scores

    return tag_to_interest_scores
