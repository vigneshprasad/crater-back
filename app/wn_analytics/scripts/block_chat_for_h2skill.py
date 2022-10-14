from users import models as user_models
from wn_analytics import constants, models


def disable_chat_for_h2skill_users(dry_run=True):

    """Disable chat for all hack2skill users who have chat active."""
    hack2skill_user_ids = models.UserSource.objects.filter(
        utm_source=constants.HACK_2_SKILL_SOURCE
    ).values_list("user_pk", flat=True)
    print("Total users: {}".format(len(hack2skill_user_ids)))

    user_permission_with_chat = user_models.UserPermission.objects.filter(
        user_id__in=hack2skill_user_ids,
        allow_chat=True
    )
    print("Total users with chat enabled: {}".format(user_permission_with_chat.count()))
    if not dry_run:
        print("Updating chat permissions")
        user_permission_with_chat.update(allow_chat=False)
        user_permission_with_chat = user_models.UserPermission.objects.filter(
            user_id__in=hack2skill_user_ids,
            allow_chat=True
        )
        print("Total users with chat enabled: {}".format(user_permission_with_chat.count()))
