from django.contrib.auth.models import Group

from users import constants
from users import models

GROUP_NAMES = [constants.WORKNETWORK_GROUP, constants.CRATER_CLUB_GROUP]


def create_groups(dry_run=True):
    """Create groups for crater club and worknetwork."""
    for group_name in GROUP_NAMES:

        print("Creating group: {}".format(group_name))
        if dry_run:
            continue

        Group.objects.get_or_create(name=group_name)


def add_users_to_group(dry_run=False):
    """Add all existing users to worknetwork group."""

    try:
        worknetwork_group = Group.objects.get(name=constants.WORKNETWORK_GROUP)
    except Group.DoesNotExist:
        create_groups(dry_run=False)
        worknetwork_group = Group.objects.get(name=constants.WORKNETWORK_GROUP)

    for user in models.User.objects.all():

        print("Adding {} to group {}".format(user.email, constants.WORKNETWORK_GROUP))

        if dry_run:
            continue
        user.groups.add(worknetwork_group)
