from resources.meetings import choices
from tags.serializers import InterestsSerializer
from tags.models import Interests


def get_objectives_list():
    objectives = [{
        'key': objective[0],
        'label': objective[1] 
    } for objective in choices.OBJECTIVE_CHOICES]
    return objectives


def get_interest_list():
    interests = InterestsSerializer(data=Interests.objects.all(), many=True)
    interests.is_valid()
    return interests.data
