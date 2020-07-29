from users import models
from users import choices


def get_admin_user():
    return models.User.objects.get(email=choices.ADMIN_USER_EMAIL)
