from resources.masterclasses.models import MasterClass
from resources.masterclasses.serializers import MasterClassSerializer


def get_first_masterclass_data():
    masterclass = MasterClass.objects.first()
    if masterclass:
        return MasterClassSerializer(masterclass).data
