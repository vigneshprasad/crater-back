import csv

from matching.engines import scoring_constants


def run(dry_run=True):
    """Creates tag to tag score in the codebase for the matching algorithm."""

    csv_file = open('/app/matching/data/tags_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tags_score_map = {}

    for row in csv_reader:

        tags = row["Tags"]
        all_tags = list(row.keys())
        # Removing tag value from each row.
        all_tags.pop(0)

        tags_score_dict = {}
        for tag in all_tags:
            tags_score_dict[tag] = row.get(tag) or 0.1
            tags_score_dict[tag] = float(tags_score_dict[tag])

        tags_score_map[tags] = tags_score_dict

    if not dry_run:
        scoring_constants.TAG_TO_TAG_SCORES = tags_score_map

    return tags_score_map
