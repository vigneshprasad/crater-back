from users import models


def run(dry_run=True):
    """Create user permissions."""
    users = models.User.objects.filter(permission__isnull=True)
    print(users.count())
    print("-----")

    for user in users:
        print(user)
        if not dry_run:
            user_permission, created = models.UserPermission.objects.get_or_create(user=user)
            print("Created user permission for user: {}".format(user_permission.id))

        print("-----")
