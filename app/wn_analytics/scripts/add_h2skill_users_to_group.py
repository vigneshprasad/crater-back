from django.contrib.auth.models import Group

from crater.auth import constants as auth_constants
from wn_analytics import constants, models


def run(dry_run=True):
    """Add all hack2skill users to hack2skill group."""
    hack2skill_user_sources = models.UserSource.objects.filter(
        utm_source=constants.HACK_2_SKILL_SOURCE
    )
    print("Total users: {}".format(hack2skill_user_sources.count()))
    hack2skill_group = Group.objects.get(name=auth_constants.HACK_2_SKILL_GROUP)
    print("Adding {} users to group {}".format(hack2skill_user_sources.count(), hack2skill_group))

    for hack2skill_user_source in hack2skill_user_sources:
        hack2skill_user = hack2skill_user_source.user
        print("Adding {} to group".format(hack2skill_user))
        if not dry_run:
            hack2skill_user.groups.add(hack2skill_group)
