import csv

from matching.engines import scoring_constants


def run(dry_run=True):
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/base_tag_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    base_tag_score_map = {}

    for row in csv_reader:

        tag = row.get("Tags")
        score = int(row.get("Score", 100))
        base_tag_score_map[tag] = score

    if not dry_run:
        scoring_constants.BASE_TAG_SCORES_FOR_USER = base_tag_score_map

    return base_tag_score_map
