import csv


def run():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/tag_company_type_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tag_to_company_type_scores = {}

    for row in csv_reader:

        tag = row["Tag-Company Type"]
        all_company_types = list(row.keys())
        # Removing the interest objective key from the row.
        all_company_types.pop(0)

        company_type_score_dict = {}
        for years_of_experience in all_company_types:
            company_type_score_dict[years_of_experience] = float(row.get(years_of_experience)) or 0.1

        tag_to_company_type_scores[tag] = company_type_score_dict

    return tag_to_company_type_scores
