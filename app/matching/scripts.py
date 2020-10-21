import csv


def create_interest_objective_tag_mapping():
    """Curates a dictionary of dictionaries from Interest objectives tags engine CSV."""
    csv_file = open('/app/matching/data/interest_objectives_tag_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    final_dictionary = {}

    for row in csv_reader:
        interest_objective = row["Interest-Objective"]
        all_tags = list(row.keys())
        all_tags.pop(0)
        tag_score_dict = {}
        for tag in all_tags:
            tag_score_dict[tag] = float(row.get(tag)) or 0.1

        final_dictionary[interest_objective] = tag_score_dict

    return final_dictionary


def create_objective_map_scores():
    """Curates a dictionary of dictionaries from Objective to objective engine CSV."""
    csv_file = open('/app/matching/data/objective_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    objective_score_map = {}

    for row in csv_reader:
        objectives = row["Objectives"]
        all_objectives = list(row.keys())
        all_objectives.pop(0)
        objective_score_dict = {}
        for objective in all_objectives:
            objective_score_dict[objective] = float(row.get(objective)) or 0.1

        objective_score_map[objectives] = objective_score_dict

    return objective_score_map


def create_tag_map_scores():
    csv_file = open('/app/matching/data/tags_map_scores.csv', mode='r')
    csv_reader = csv.DictReader(csv_file)
    tags_score_map = {}

    for row in csv_reader:
        tags = row["Tags"]
        all_tags = list(row.keys())
        all_tags.pop(0)
        tags_score_dict = {}
        for tag in all_tags:
            tags_score_dict[tag] = row.get(tag) or 0.1
            tags_score_dict[tag] = float(tags_score_dict[tag])

        tags_score_map[tags] = tags_score_dict

    return tags_score_map
