from users import choices
from users import models
from users import signals


def run(dry_run=True):
    for typeform_url, source in choices.TYPEFORM_URL_TO_SOURCE_MAP.iteritems():
        print("Mapping {} to ---- {}".format(typeform_url, source))
        users = models.User.objects.filter(source=typeform_url)
        print("User's being updated: {}".format(users.count()))
        if not dry_run:
            users.update(source=source)


def run_analytics(dry_run=True, users=None):
    users = models.User.objects.filter(source__in=choices.TYPEFORM_URL_TO_SOURCE_MAP.values()) if not users else users
    print("Number of users being update on analytics: {}".format(users.count()))
    for user in users:
        print("Updating user: {}".format(user.email))
        if not dry_run:
            signals.user_updated.send(
                sender=user.user.__class__,
                user=user
            )
