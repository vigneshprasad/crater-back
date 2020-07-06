from .serializers import UserTraitsSerializer

def get_user_traits(user):
    traits = UserTraitsSerializer(user).data
    return traits
