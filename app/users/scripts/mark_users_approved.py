from users import models


def run(dry_run=False):
    total_users = models.User.objects.filter(phone_number_verified=True)
    print("Total user's being approved: {}".format(total_users.count()))

    for user in models.User.objects.filter(phone_number_verified=True):
        print(user.email)
        if not dry_run:
            user.set_phone_number_verified()
