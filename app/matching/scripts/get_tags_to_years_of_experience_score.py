import csv

from matching.engines import new_scoring_constants
from users.scripts import fix_new_tag_for_users

TAG_MAP = fix_new_tag_for_users.TAGS_TO_NEW_TAGS_MATCH


def run(dry_run=False):
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/user_score_temp_calculate.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        email = row["Email"]
        tag = row["Tag"]
        experience = row["Experience"] or 0
        new_tag = TAG_MAP.get(tag, "Others")
        score = new_scoring_constants.TAG_TO_EXPERIENCE_SCORES[new_tag][int(experience)]
        print(email, ",", score)
