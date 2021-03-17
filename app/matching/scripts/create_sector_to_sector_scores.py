import csv


def run():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""

    csv_file = open('/app/matching/data/sector_to_sector_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    sector_to_sector_scores = {}

    for row in csv_reader:
        print(row)
        sector_to_sector = row["Sector-Sector"]
        all_sectors = list(row.keys())
        # Removing the interest objective key from the row.
        all_sectors.pop(0)
        sector_score_dict = {}
        for sector in all_sectors:
            sector_score_dict[sector] = int(row.get(sector, 0) or 0)

        sector_to_sector_scores[sector_to_sector] = sector_score_dict

    return sector_to_sector_scores
