from django.contrib.auth import get_user_model


def run(dry_run=True):

    users = get_user_model().objects.all()

    for user in users:
        print("Start", "*"*10)

        print("User: {}".format(user.email))
        phone_number = user.get_phone_number()

        if not phone_number:
            print("User has no phone number: {}".format(user.email))

        print("Changing username from {} to {}".format(user.username, phone_number))

        if not dry_run:
            user.username = phone_number
            user.save()

        print("End", "*" * 10)
