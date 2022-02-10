from users import models
from users import constants


def run():
    # Data is returned in CSV format.
    users = models.User.objects.all().order_by("username")

    for user in users:
        date_joined_display = user.date_joined.strftime("%A, %d %B")
        is_crater = user.groups.filter(name=constants.CRATER_CLUB_GROUP).exists()
        print(
            user.pk, "#",
            user.username, "#",
            user.email, "#",
            user.phone_number, "#",
            date_joined_display, "#",
            is_crater
        )
