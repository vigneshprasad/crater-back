import csv


def run():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/tag_experience_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tag_to_experience_scores = {}

    for row in csv_reader:

        tag = row["Tag-Experience"]
        all_years_of_experience = list(row.keys())
        # Removing the interest objective key from the row.
        all_years_of_experience.pop(0)

        year_of_experience_score_dict = {}
        for years_of_experience in all_years_of_experience:
            year_of_experience_score_dict[years_of_experience] = float(row.get(years_of_experience)) or 0.1

        tag_to_experience_scores[tag] = year_of_experience_score_dict

    return tag_to_experience_scores
