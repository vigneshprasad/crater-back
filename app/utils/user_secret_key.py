import uuid

from django.conf import settings
from rest_framework_jwt.utils import jwt_payload_handler as payload_handler


def create_new_secret_key():
    new_uuid_part1 = uuid.uuid4()
    new_uuid_part2 = uuid.uuid4()
    return f'{new_uuid_part1}_{str(new_uuid_part2)}'


def get_user_secret_key(user):
    return user.auth_secret_key if user.auth_secret_key else settings.SECRET_KEY


def jwt_payload_handler(user):
    from users.serializers import UserDetailSerializer
    payload = payload_handler(user)
    data = UserDetailSerializer(user).data
    payload.update(**data)
    return payload
