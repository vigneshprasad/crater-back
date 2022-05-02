from users import models


def run(dry_run=True):
    """Create user permissions."""
    users = models.User.objects.filter(user_permission__isnull=False)
    print(users.count())

    for user in users:
        print("-----")
        print(user)
        if not dry_run:
            user_permission, created = models.UserPermission.objects.get_or_create(user=user)
            print("Created user permission for user: {}".format(user_permission.id))

        print("-----")
