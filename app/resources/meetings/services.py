from resources.meetings import choices


def get_objectives_list():
    objectives = [objective[1] for objective in choices.OBJECTIVE_CHOICES]
    return objectives
