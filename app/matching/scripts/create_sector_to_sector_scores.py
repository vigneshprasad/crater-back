import csv


def run():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/sector_to_sector_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    sector_to_sector_scores = {}

    for row in csv_reader:
        print(row)
        interest_objective = row["Sector-Sector"]
        all_tags = list(row.keys())
        # Removing the interest objective key from the row.
        all_tags.pop(0)
        tag_score_dict = {}
        for tag in all_tags:
            tag_score_dict[tag] = int(row.get(tag, 0) or 0)

        sector_to_sector_scores[interest_objective] = tag_score_dict

    return sector_to_sector_scores
